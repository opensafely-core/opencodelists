import shutil
import sys
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from codelists.coding_systems import CODING_SYSTEMS
from codelists.models import CodelistVersion
from codelists.search import do_search
from coding_systems.versioning.models import (
    CodingSystemRelease,
    ReleaseState,
    update_coding_system_database_connections,
)


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

    def __init__(self, coding_system, release_name, valid_from, import_ref):
        self.coding_system = coding_system
        self.release_name = release_name
        self.valid_from = valid_from
        self.import_ref = import_ref or ""
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
    new_coding_system = CODING_SYSTEMS[coding_system_id](
        database_alias=new_database_alias
    )
    """
    Check compatibility of existing codelist versions with a new coding system release

    Filter codelist versions to only those that
    1) have searches and
    2) are compatible with, or created from, the previous release

    Note we don't exlude version created from or already in the compatible
    set for THIS release.  If we're doing a forced-overwrite import (which is where
    we'd expect that might happen), we want to re-check compatibility
    """
    previous_release = (
        CodingSystemRelease.objects.filter(coding_system=coding_system_id)
        .exclude(id=new_coding_system.release.id)
        .latest("valid_from")
    )
    versions_with_searches = set(
        CodelistVersion.objects.filter(
            Q(codelist__coding_system_id=coding_system_id, searches__isnull=False)
            & (
                Q(compatible_releases__id=previous_release.id)
                | Q(coding_system_release=previous_release)
            )
        )
    )

    compatible_count = 0
    number_of_versions = len(versions_with_searches)
    for i, version in enumerate(versions_with_searches, start=1):
        update_progress(i, number_of_versions, comment="Checking compatibility: ")
        compatible = True

        for search in version.searches.all():
            current_codes = set(search.results.values_list("code_obj__code", flat=True))
            updated_codes = do_search(
                new_coding_system, term=search.term, code=search.code
            )["all_codes"]
            if current_codes != updated_codes:
                compatible = False
                break

        if compatible:
            version.compatible_releases.add(new_coding_system.release)
            compatible_count += 1

    print(
        f"{len(versions_with_searches)} codelist versions with searches checked; {compatible_count} identified as compatible"
    )


def update_progress(count, total, comment=None, bar_length=30):
    comment = comment or ""
    progress = count / total
    hashes = "#" * int(round(progress * bar_length))
    spaces = " " * (bar_length - len(hashes))
    sys.stdout.write(
        f"\r{comment}[{hashes + spaces}] {int(round(progress * 100))}% {count}/{total}"
    )
    if count == total:
        sys.stdout.write("\n")
    sys.stdout.flush()
