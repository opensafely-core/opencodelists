import shutil
from itertools import islice
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from tqdm import tqdm

from codelists.coding_systems import CODING_SYSTEMS
from codelists.hierarchy import Hierarchy
from codelists.models import CodelistVersion, Status
from codelists.search import do_search
from coding_systems.versioning.models import (
    CodingSystemRelease,
    ReleaseState,
    update_coding_system_database_connections,
)


def batched_bulk_create(model, database_alias, iter_records, batch_size=999):
    """
    Batch records into groups of at most batch_size (defaulting to 999 - the sqlite max)
    for bulk_create.
    """
    while True:
        batch = list(islice(iter_records, batch_size))
        if not batch:
            break
        model.objects.using(database_alias).bulk_create(batch, batch_size)


class CodingSystemImporter:
    """
    A context manager that deals with:
    Setup before importing a new release:
     - generating/retrieving the CodingSystemRelease instance (and the associated database_alias)
     - ensuring the new database schema is created
    Final clean up if anything goes wrong
    Final update of the CodingSystemRelease with import timestamp and refs once the import
    is complete.
    """

    def __init__(
        self,
        coding_system,
        release_name,
        valid_from,
        import_ref,
        check_compatibility=True,
    ):
        self.coding_system = coding_system
        self.release_name = release_name
        self.valid_from = valid_from
        self.import_ref = import_ref or ""
        self.check_compatibilty = check_compatibility
        self.import_datetime = timezone.now()
        self.cs_release = None
        self.new_db_path = None
        self.backup_path = None

    def __enter__(self):
        # return the database_alias after setting up the new import db
        try:
            self.setup_new_import_database()
            print(f"Importing {self.coding_system} data...")
            return self.cs_release.database_alias
        except Exception:
            # if anything went wrong during the setup, ensure that any paths have been reset
            if self.backup_path is not None:
                shutil.copy(self.backup_path, self.new_db_path)
                self.backup_path.unlink()
            elif self.new_db_path is not None and self.new_db_path.exists():
                self.new_db_path.unlink()
            raise

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_value:
            # If anything went wrong, revert to the initial state
            if self.backup_path is not None:
                # there was an existing database (i.e. this import was a forced-overwrite of an
                # existing one).  Revert the database to the backup, and leave the CodingSystemRelease
                # in place.  Timestamps and refs have not been updated yet, so the CodingSystemRelease
                # represents the state of the previous import.
                shutil.copy(self.backup_path, self.new_db_path)
                self.backup_path.unlink()
            else:
                # if there was no existing db, remove the failed new db file and delete the CodingSystemRelease
                self.cs_release.delete()
                self.new_db_path.unlink()
            # raise the exception
            return False
        # Finally, if all went well, update the coding system release fields
        self.cs_release.state = ReleaseState.READY
        self.cs_release.import_timestamp = self.import_datetime
        self.cs_release.import_ref = self.import_ref
        self.cs_release.save()

        if self.backup_path is not None:
            self.backup_path.unlink()

        if self.check_compatibilty:
            # Finally, now that the data has been imported successfully, check any existing
            # codelist versions for compatibility
            update_codelist_version_compatibility(
                self.coding_system, self.cs_release.database_alias
            )

    @transaction.atomic
    def setup_new_import_database(self):
        """
        This method deals with the setup for importing a new coding system release:
        - gets/creates the CodingSystemRelease object
        - updates the database connections with the new release database
        - for re-imports, backs up the existing database file
        - runs migrate on the new database file to create the expected tables
        """
        print("Setting up database...")

        # get or create the CodingSystemRelease; a CodingSystemRelease may already exist
        # if we are re-importing (and overwriting) an existing release
        #
        # Note that we don't update an existing CodingSystemRelease with a new import_timestamp
        # or import_ref yet, in case something goes wrong during the import and it needs to be
        # rolled back.
        #
        # Also Note that this method is wrapped in transaction.atomic, but this will ONLY
        # roll back the CodingSystemRelease object in case of errors raised in this
        # method itself.  The __exit__ method deals with reverting the state of the
        # release database if anything goes wrong during the data import.
        self.cs_release, _ = CodingSystemRelease.objects.get_or_create(
            coding_system=self.coding_system,
            release_name=self.release_name,
            valid_from=self.valid_from,
            defaults={
                "import_timestamp": self.import_datetime,
                "import_ref": self.import_ref,
            },
        )
        self.cs_release.state = ReleaseState.IMPORTING
        self.cs_release.save()

        # ensure the new database connection is available
        update_coding_system_database_connections()
        database_alias = self.cs_release.database_alias

        # make sure the coding system directory exists
        coding_system_dir = Path(
            settings.CODING_SYSTEMS_DATABASE_DIR / self.coding_system
        )
        coding_system_dir.mkdir(parents=True, exist_ok=True)

        # If this is a forced-rerun of a coding system import, the db file will be there
        # already.  We want to start with a blank slate, but in case the new import fails,
        # we also want to revert to the previous state, so we backup the db file first, so
        # that we can restore it later if necessary.
        # Note that we don't wrap these commands in `transaction.atomic`, because we're always
        # creating a whole new database.  We can't use transaction.atomic to rollback creation
        # of the CodingSystemRelease if the import fails, because it lives in a different
        # database to the coding system tables we're importing to.
        self.new_db_path = coding_system_dir / f"{database_alias}.sqlite3"
        self.backup_path = None
        if self.new_db_path.exists():
            self.backup_path = self.new_db_path.with_suffix(".sqlite3.bu")
            shutil.copy(self.new_db_path, self.backup_path)
            self.new_db_path.unlink()
        # run migrate to create the tables
        call_command("migrate", self.coding_system, database=database_alias)

        return database_alias


def update_codelist_version_compatibility(coding_system_id, new_database_alias):
    """
    Check compatibility of existing codelist versions with a new coding system release

    Filter codelist versions to only those that are compatible with, or created from,
    the previous release. Any codelist versions that were not compatible with the previous
    release can ignored, as we wouldn't expect them to be compatible with any later releases.
    We can only check versions that have hierarchies for compatibility.

    Note we don't exclude versions created from, or already in the compatible
    set, for THIS release.  If we're doing a forced-overwrite import (which is where
    we'd expect that might happen), we want to re-check compatibility.

    The compatibility check is conservative.  All we're aiming to do here is to say
    that a codelist version with the same codes and searches, would look the same in this
    new release of the coding system.  In order to do this, we check both its search
    results and its hierarchy, which represents the section of the coding system extended
    both parent-wise and child-wise from the associated codes on the codelist version.

    We do NOT check versions that are in draft status, as they are subject to change.
    Drafts are built/created with a specific coding system release, and any additional
    searches and included/excluded codes will be made with its assigned coding system
    release. When a draft is moved to under-review or published, its codes will not change,
    so it can be checked for compatibility against any newer releases at that point.

    To determine compatibility, we check:
    1) That a hierarchy built from the codelist version's codes is identical
    This indicates that the section of the coding system that relates to any code in
    the codelist (included OR excluded) is identical in the new release.
    CodelistVersion.codes represents all of a codelist version's included codes, however its
    codeset includes any descendants of those codes, whether included or excluded.
    A codelist's hierarchy is built in both directions, so it will include all parents right
    up to the root node, as well as the included/excluded code objs
    AND
    2) if the version has searches, rerun the searches with the new release and check that the
    results are the same

    """
    new_coding_system = CODING_SYSTEMS[coding_system_id](
        database_alias=new_database_alias
    )
    # Filter to under-review and published versions compatible with previous release
    versions_to_check, previous_release = get_versions_compatible_with_previous(
        new_coding_system
    )
    print(
        f"Found {len(versions_to_check)} versions compatible with previous release '{previous_release.database_alias}'."
    )

    compatible_count = check_and_update_compatibile_versions(
        new_coding_system, versions_to_check
    )
    print(
        f"{len(versions_to_check)} checked; {compatible_count} identified as compatible"
    )


def get_versions_compatible_with_previous(coding_system):
    """Find all under-review and published versions compatible with previous release"""
    previous_release = (
        CodingSystemRelease.objects.filter(
            coding_system=coding_system.id,
            valid_from__lt=coding_system.release.valid_from,
        )
        .exclude(id=coding_system.release.id)
        .latest("valid_from")
    )
    versions = set(
        CodelistVersion.objects.exclude(status=Status.DRAFT).filter(
            Q(compatible_releases__id=previous_release.id)
            | Q(coding_system_release=previous_release)
        )
    )
    return versions, previous_release


def version_is_compatible_with_coding_system_release(coding_system, version):
    """
    Determine whether a single version is considered compatible with a specific coding system
    release
    """
    if not version.has_hierarchy:
        # if there's no hierarchy to check against, we can't say it's compatible
        return False
    # First check the hierarchies match, and then check any searches return the same results
    return _check_version_by_search(
        coding_system, version
    ) and _check_version_by_hierarchy(coding_system, version)


def check_and_update_compatibile_versions(coding_system, versions):
    """
    Check compatibility of a set of codelist versions against a specific coding system release
    Update the compatible_releases for any version found to be compatible
    """
    compatible_count = 0
    for version in tqdm(versions):
        if version_is_compatible_with_coding_system_release(coding_system, version):
            version.compatible_releases.add(coding_system.release)
            compatible_count += 1
    return compatible_count


def _check_version_by_hierarchy(coding_system, version):
    r"""
    Check the compatibility of a codelist version with a specific coding system release
    by comparing the hierarchy generated from its codes.

    The version is compatible (on the basis of hierarchy) if
    a hierarchy built from the version's coding system release and included codes is
    identical to a hierarchy built from the comparison coding system release and the
    version's included codes.

    A hierarchy generated from a set of codes represents a subset of the coding system that
    includes all ancestors (up to the coding system's root node) and descendants of each code.

    e.g. For a coding system with this structure
           a
          / \
         b   c
        / \ / \
       d   e   f

    A codelist version that includes just the code 'f' will have the following hierarchy:
           a
            \
             c
              \
               f

    If there is a change in a different branch of the coding system - e.g. code 'd' is
    removed, will not affect the codelist version's hierarchy, and it will be considered
    compatible.

    However, if a change occurs in the branch that includes 'f', e.g. there is a new
    descendant code, 'g', the hierarchy will differ and the codelist version will be
    considered incompatible:
           a
          / \
         b   c
        / \ / \
       d   e   f
                \
                 g

    In the above case, there is now a new descendant code that needs to be included/excluded
    in the codelist version.

    If a change occurs in the ancestors of the included code 'f', e.g. 'c' is replaced by 'x':
           a
          / \
         b   x
        / \ / \
       d   e   f

    The hierarchy has changed, and the codelist version will be considered incompatible, even
    though there are no new descendant codes that need to be included or excluded.

    Note that our compatibility check is conservative and the fact that it is does not pass
    the compatiblity check does not mean that a new codelist version cannot be successfully
    created from this one with the new coding system release.

    Note that overall compatibility is determined based on both identical search results
    and identical hierarchies.
    """

    # All codelist versions that existed prior to implementation of coding system releases
    # have an "unknown" coding system release, which represents the coding system data at that
    # point. For older codelist versions, that is not the actual coding system release that was
    # used to create the codelist version, and we do not have a record of, or access to, the
    # coding system data at the time of its creation.
    # All existing codelist versions, including those with the "unknown" coding system release,
    # will have a cached hierarchy, built with the original coding system release.
    # We compare this to a hierarchy built from the same codes, but with the new release.

    return version.hierarchy == Hierarchy.from_codes(coding_system, version.codes)


def _check_version_by_search(coding_system, version):
    """
    Check the compatibility of a codelist version with a specific coding system release
    by rerunning its searches.  The version is compatible (on the basis of searches) if
    the search results are identical when run with the version's coding system release and
    with the comparison coding system release.

    A search finds codes in the coding system that match a specific term or code, AND all
    their descendant codes (returned in the search results as "all_codes").

    Note that overall compatibility is determined based on both identical search results
    and identical hierarchies.
    """
    for search in version.searches.all():
        current_codes = set(search.results.values_list("code_obj__code", flat=True))
        updated_codes = do_search(coding_system, term=search.term, code=search.code)[
            "all_codes"
        ]
        if current_codes != updated_codes:
            return False
    return True
