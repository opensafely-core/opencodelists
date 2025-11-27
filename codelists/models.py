import hashlib

from django.contrib.auth.models import AnonymousUser
from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.functional import cached_property
from taggit.managers import TaggableManager

from mappings.bnfdmd.mappers import bnf_to_dmd
from mappings.dmdvmpprevmap.mappers import vmpprev_full_mappings
from opencodelists.csv_utils import (
    csv_data_to_rows,
    dict_rows_to_csv_data,
    rows_to_csv_data,
)
from opencodelists.hash_utils import hash, unhash

from .codeset import Codeset
from .coding_systems import CODING_SYSTEMS, most_recent_database_alias
from .hierarchy import Hierarchy


class Codelist(models.Model):
    CODING_SYSTEMS_CHOICES = sorted(
        (id, system.name) for id, system in CODING_SYSTEMS.items()
    )

    coding_system_id = models.CharField(
        choices=CODING_SYSTEMS_CHOICES, max_length=32, verbose_name="Coding system"
    )
    description = models.TextField(null=True, blank=True)
    methodology = models.TextField(null=True, blank=True)
    is_private = models.BooleanField(default=False)
    tags = TaggableManager()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @cached_property
    def coding_system_cls(self):
        # Returns the coding system class for this codelist
        # This provides access to persistent features of the coding system
        # e.g. name, id, but is not associated with a specific version of the system
        return CODING_SYSTEMS[self.coding_system_id]

    @cached_property
    def coding_system_short_name(self):
        return self.coding_system_cls.short_name

    @property
    def codelist_type(self):
        if self.user_id:
            assert not self.organisation_id
            return "user"
        else:
            assert self.organisation_id
            return "organisation"

    @cached_property
    def current_handle(self):
        if (
            hasattr(self, "_prefetched_objects_cache")
            and "handles" in self._prefetched_objects_cache
        ):
            current_handles = [h for h in self.handles.all() if h.is_current]
            assert len(current_handles) == 1
            return current_handles[0]
        return self.handles.filter(is_current=True).get()

    @cached_property
    def owner(self):
        return self.current_handle.owner

    @property
    def name(self):
        return self.current_handle.name

    @property
    def slug(self):
        return self.current_handle.slug

    @property
    def user_id(self):
        return self.current_handle.user_id

    @property
    def user(self):
        return self.current_handle.user

    @property
    def organisation_id(self):
        return self.current_handle.organisation_id

    @property
    def organisation(self):
        return self.current_handle.organisation

    def get_absolute_url(self):
        return reverse(
            f"codelists:{self.codelist_type}_codelist", kwargs=self.url_kwargs
        )

    def get_latest_published_url(self):
        """
        Return the URL for the latest published version, or if no such version exists,
        return the absolute URL for this codelist, which will redirect to the user's latest
        visible version
        """
        if self.latest_published_version():
            return self.latest_published_version().get_absolute_url()
        return self.get_absolute_url()

    def get_update_url(self):
        return reverse(
            f"codelists:{self.codelist_type}_codelist_update", kwargs=self.url_kwargs
        )

    def get_clone_url(self):
        return reverse(
            f"codelists:{self.codelist_type}_codelist_clone", kwargs=self.url_kwargs
        )

    def get_version_upload_url(self):
        return reverse(
            f"codelists:{self.codelist_type}_version_upload", kwargs=self.url_kwargs
        )

    def get_versions_api_url(self):
        return reverse(
            f"codelists_api:{self.codelist_type}_versions", kwargs=self.url_kwargs
        )

    @property
    def url_kwargs(self):
        if self.codelist_type == "organisation":
            return {
                "organisation_slug": self.organisation_id,
                "codelist_slug": self.slug,
            }
        else:
            return {
                "username": self.user_id,
                "codelist_slug": self.slug,
            }

    def full_slug(self):
        if self.codelist_type == "organisation":
            return f"{self.organisation_id}/{self.slug}"
        else:
            return f"user/{self.user_id}/{self.slug}"

    def is_new_style(self):
        return self.versions.filter(csv_data__isnull=True).exists()

    def can_be_edited_by(self, user):
        """Return whether codelist can be edited by given user.

        A codelist can be edited by a user if:

            * the user is authenticated
            * the user is a collaborator on the codelist
            * the codelist is owned by the user
            * the codelist is owned by one of the organisations the user is a member of
        """

        if not user.is_authenticated:
            return False

        if self.collaborations.filter(collaborator=user).exists():
            return True

        if self.codelist_type == "user":
            return user == self.user
        else:
            return user.is_member(self.organisation)

    def visible_versions(
        self,
        user,
        include_version_id: int | None = None,
    ) -> models.QuerySet["CodelistVersion"]:
        """Return all versions visible to the user, with newest first.

        If the user can edit the codelist, all versions are returned.
        Otherwise, only published versions are returned, plus the one
        corresponding to the `include_version_id` if provided.
        """
        versions = self.versions.order_by("-id")

        if self.can_be_edited_by(user):
            return versions

        q = Q(status=Status.PUBLISHED)
        if include_version_id is not None:
            q |= Q(id=include_version_id)

        return versions.filter(q)

    def latest_visible_version(self, user):
        """Return latest version visible to the user, or None if no such version
        exists."""

        return self.visible_versions(user).first()

    def latest_published_version(self):
        """Return URL latest published version, or None if no such version exists."""
        # the latest visible version for an anonymous user will be the latest published one
        published = self.visible_versions(user=AnonymousUser())
        return published.first()

    def has_published_versions(self):
        return self.versions.filter(status="published").exists()


class Handle(models.Model):
    codelist = models.ForeignKey(
        "Codelist", on_delete=models.CASCADE, related_name="handles"
    )
    name = models.CharField(
        max_length=255,
        validators=[
            RegexValidator(
                # Codelist names get slugified, which must result in a valid slug.
                # Let's require alphanumeric characters as it's easier to explain.
                regex=r"[a-zA-Z0-9]+",
                message="Codelist names must contain at least one letter or number.",
            )
        ],
    )
    slug = models.SlugField(max_length=255)
    organisation = models.ForeignKey(
        "opencodelists.Organisation",
        null=True,
        related_name="handles",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        "opencodelists.User",
        null=True,
        related_name="handles",
        on_delete=models.CASCADE,
    )
    is_current = models.BooleanField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [
            ("organisation", "slug"),
            ("organisation", "name"),
            ("user", "slug"),
            ("user", "name"),
        ]
        constraints = [
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_organisation_xor_user",
                condition=(
                    models.Q(organisation_id__isnull=False, user_id__isnull=True)
                    | models.Q(user_id__isnull=False, organisation_id__isnull=True)
                ),
            )
        ]

    @cached_property
    def owner(self):
        return self.organisation or self.user


class Status(models.TextChoices):
    DRAFT = "draft"  # the version is being edited in the builder
    UNDER_REVIEW = "under review"  # the version is being reviewed
    PUBLISHED = "published"  # the version has been published and cannot be deleted


class CodelistVersion(models.Model):
    codelist = models.ForeignKey(
        "Codelist", on_delete=models.CASCADE, related_name="versions"
    )

    coding_system_release = models.ForeignKey(
        "versioning.CodingSystemRelease",
        related_name="codelist_versions",
        on_delete=models.CASCADE,
    )
    compatible_releases = models.ManyToManyField("versioning.CodingSystemRelease")

    status = models.CharField(max_length=len("under review"), choices=Status.choices)

    # The user who created this version
    author = models.ForeignKey(
        "opencodelists.User",
        related_name="versions",
        on_delete=models.CASCADE,
        null=True,
    )
    tag = models.CharField(max_length=12, null=True)
    csv_data = models.TextField(verbose_name="CSV data", null=True)

    cached_csv_data = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("codelist", "tag")

    class Manager(models.Manager):
        def get_by_hash(self, hash):
            """Return the CodelistVersion with given hash."""
            id = unhash(hash, "CodelistVersion")
            return self.get(id=id)

    objects = Manager()

    def save(self, *args, **kwargs):
        if self.csv_data:
            self.csv_data = self.csv_data.replace("\r\n", "\n")
        super().save(*args, **kwargs)

    @property
    def organisation(self):
        return self.codelist.organisation

    @property
    def user(self):
        return self.codelist.user

    def get_absolute_url(self):
        return reverse(
            f"codelists:{self.codelist_type}_version", kwargs=self.url_kwargs
        )

    def get_publish_url(self):
        return reverse(
            f"codelists:{self.codelist_type}_version_publish", kwargs=self.url_kwargs
        )

    def get_delete_url(self):
        return reverse(
            f"codelists:{self.codelist_type}_version_delete", kwargs=self.url_kwargs
        )

    def get_download_url(self):
        return reverse(
            f"codelists:{self.codelist_type}_version_download", kwargs=self.url_kwargs
        )

    def get_download_definition_url(self):
        return reverse(
            f"codelists:{self.codelist_type}_version_download_definition",
            kwargs=self.url_kwargs,
        )

    def get_dmd_download_url(self):
        return reverse(
            f"codelists:{self.codelist_type}_version_dmd_download",
            kwargs=self.url_kwargs,
        )

    def get_dmd_convert_url(self):
        return reverse(
            f"codelists:{self.codelist_type}_version_dmd_convert",
            kwargs=self.url_kwargs,
        )

    def get_create_url(self):
        return reverse(
            f"codelists:{self.codelist_type}_version_create", kwargs=self.url_kwargs
        )

    def get_builder_draft_url(self):
        return reverse("builder:draft", args=[self.hash])

    def get_builder_update_url(self):
        return reverse("builder:update", args=[self.hash])

    def get_builder_new_search_url(self):
        return reverse("builder:new-search", args=[self.hash])

    def get_builder_search_url(self, search_id, search_slug):
        return reverse("builder:search", args=[self.hash, search_id, search_slug])

    def get_builder_delete_search_url(self, search_id, search_slug):
        return reverse(
            "builder:delete-search", args=[self.hash, search_id, search_slug]
        )

    def get_builder_no_search_term_url(self):
        return reverse("builder:no-search-term", args=[self.hash])

    def get_diff_url(self, other_clv):
        kwargs = self.url_kwargs
        kwargs["other_tag_or_hash"] = other_clv.tag_or_hash
        return reverse(f"codelists:{self.codelist_type}_version_diff", kwargs=kwargs)

    def exists(self):
        """
        Check that this CodelistVersion exists in the database.  It may not, in the event that it's just
        been discarded
        """
        return CodelistVersion.objects.filter(id=self.id).exists()

    @property
    def url_kwargs(self):
        kwargs = self.codelist.url_kwargs
        kwargs["tag_or_hash"] = self.tag_or_hash
        return kwargs

    @property
    def hash(self):
        return hash(self.id, "CodelistVersion")

    @property
    def tag_or_hash(self):
        return self.tag or self.hash

    @cached_property
    def coding_system_id(self):
        return self.codelist.coding_system_id

    @cached_property
    def coding_system(self):
        return self.codelist.coding_system_cls(
            database_alias=self.coding_system_release.database_alias
        )

    @property
    def codelist_type(self):
        return self.codelist.codelist_type

    def full_slug(self):
        return f"{self.codelist.full_slug()}/{self.tag_or_hash}"

    @property
    def has_hierarchy(self):
        return self.coding_system.is_builder_compatible()

    def calculate_hierarchy(self):
        """Return Hierarchy of codes related to this CodelistVersion."""
        if self.csv_data:
            return self._calculate_old_style_hierarchy()
        else:
            return self._calculate_new_style_hierarchy()

    def _calculate_old_style_hierarchy(self):
        if not self.has_hierarchy:
            # If coding system does not define relationships, then we cannot build a
            # hierarchy, and so it's not clear what a hierarchy is for.
            return

        return Hierarchy.from_codes(self.coding_system, self.codes)

    def _calculate_new_style_hierarchy(self):
        code_to_status = dict(self.code_objs.values_list("code", "status"))
        return Hierarchy.from_codes(self.coding_system, list(code_to_status))

    @cached_property
    def hierarchy(self):
        """Return Hierarchy of codes related to this CodelistVersion.

        It is expected that this version will already have a corresponding
        cached_hierarchy object.
        """
        return Hierarchy.from_cache(self.cached_hierarchy.data)

    @property
    def codeset(self):
        """Return Codeset for the codes related to this CodelistVersion."""

        if self.csv_data:
            return self._old_style_codeset()
        else:
            return self._new_style_codeset()

    def _old_style_codeset(self):
        if not self.has_hierarchy:
            # If coding system does not define relationships, then we cannot build a
            # hierarchy, and so it's not clear what a codeset is for.
            return

        return Codeset.from_codes(set(self.codes), self.hierarchy)

    def _new_style_codeset(self):
        code_to_status = dict(self.code_objs.values_list("code", "status"))
        return Codeset(code_to_status, self.hierarchy)

    @property
    def table(self):
        if self.csv_data:
            return self._old_style_table()
        else:
            return self._new_style_table()

    def _old_style_table(self):
        return csv_data_to_rows(self.csv_data)

    def _new_style_table(self):
        code_to_term = self.coding_system.code_to_term(self.codes)
        rows = [["code", "term"]]
        rows.extend([code, code_to_term.get(code, "[Unknown]")] for code in self.codes)
        return rows

    @property
    def downloadable(self):
        if self.status == Status.DRAFT:
            return False
        if not self.csv_data:
            return True
        first_row = {header.lower() for header in self.table[0]}
        possible_code_headers = set(self.codelist.coding_system_cls.csv_headers["code"])
        return bool(first_row & possible_code_headers)

    @cached_property
    def codes(self):
        if self.csv_data:
            return self._old_style_codes()
        else:
            return self._new_style_codes()

    def _old_style_codes(self):
        if self.coding_system.is_builder_compatible():
            headers, *rows = self.table
            headers = [header.lower().strip() for header in headers]
            # old style codelists are now required to contain a column named "code"
            # However, older ones could be uploaded with any column names, so we need to
            # check the headers to identify the most likely one
            # These represent the valid case-insensitive code column names across all existing
            # old-style codelists
            ix = 0
            for header in [
                "ctv3id",
                "ctv3code",
                "ctv3_id",
                "snomedct_id",
                "snomedcode",
                "snomed_id",
                "dmd",
                "dmd_id",
                "icd10",
                "icd code",
                "icd_code",
                "icd",
                "icd10_code",
                "id",
                "code",
            ]:
                if header in headers:
                    ix = headers.index(header)
                    break
            else:
                if self.codelist.slug == "ethnicity":
                    ix = 1
                elif self.coding_system_id == "dmd":
                    # som old dm+d codelist versions were uploaded with minimal checks, this attempts
                    # to account for those that were uploaded without a header (i.e. the header is row data)
                    # the easiest way to detect this is numeric data (i.e. dm+d IDs) in the header
                    for header in headers:
                        if header.isnumeric():
                            ix = headers.index(header)
                            rows = [headers] + rows
                            break

            return tuple(sorted({row[ix] for row in rows}))

    def _new_style_codes(self):
        return tuple(sorted(self.codeset.codes()))

    def csv_data_for_download(self, fixed_headers=False, include_mapped_vmps=True):
        """
        Prepare codes for download.  If this is a new-style codelist, the csv data with
        code and related term will be built from the code objects, looking up the terms in
        the coding system.  If it is an old-style codelist, it has no associated code objects,
        and it will use the uploaded csv_data.

        include_mapped_vmps: if True, a dm+d codelist will include mapped VMPs in its download.
          This value defaults to True, so that when these downloads are requested by OpenSafely CLI,
          no additional query params need to be passed that are specific to dm+d codelists.
        fixed_headers: if True, uploaded csv_data for old-style codelists is converted
          to two columns, headed "code" and "term". Note that new-style codelists, will
          always download with just "code" and "term" headers.
        """
        dmd_version_needs_refreshed = (
            self.coding_system_id == "dmd"
            and include_mapped_vmps
            and self.cached_csv_data.get("release") != most_recent_database_alias("dmd")
        )
        cache_key = f"download_data_fixed_headers_{fixed_headers}_include_mapped_vmps_{include_mapped_vmps}"
        if not self.cached_csv_data.get(cache_key) or dmd_version_needs_refreshed:
            if self.csv_data:
                dmd_with_mapped_vmps = (
                    self.coding_system_id == "dmd" and include_mapped_vmps
                )
                if not fixed_headers and not dmd_with_mapped_vmps:
                    csv_data = self.csv_data
                else:
                    csv_data = rows_to_csv_data(
                        self.formatted_table(
                            fixed_headers=fixed_headers,
                            include_mapped_vmps=include_mapped_vmps,
                        )
                    )
            else:
                csv_data = rows_to_csv_data(self.table)
            relevant_release = (
                most_recent_database_alias("dmd")
                if self.coding_system_id == "dmd"
                else self.coding_system_release.database_alias
            )
            self.cached_csv_data.update(
                {
                    cache_key: csv_data,
                    "release": relevant_release,
                }
            )
            self.save()
        return self.cached_csv_data[cache_key]

    def csv_data_sha(self, csv_data=None):
        """
        sha of CSV data for download with default parameters. This matches the method
        used to hash the CSVs downloaded in a study repo.
        # In order to avoid different OS messing with line endings, opensafely-cli
        # splits the lines and rejoins them before hashing.
        """
        csv_data = csv_data or self.csv_data_for_download()
        data_for_download = "\n".join(csv_data.splitlines())
        return hashlib.sha1(data_for_download.encode()).hexdigest()

    def _get_dmd_shas(self, shas, current_csv_data_download):
        """
        Return valid shas for a dm+d codelist CSV download

        This is used to check whether an existing downloaded CSV for this
        dm+d version (i.e. a download in a study repo) is still up-to-date.
        dm+d VMPs can change with each weekly dm+d release, so downloads
        need to include any mapped VMPs, in addition to the original ones in
        the codelist. Due to historic changes in the way the default download
        is formatted, there are multiple formats of the download that could
        be considered valid, as they include all relevant mapped VMPs at the
        time of this release.  These include:
        - "old-style" downloads - these were just a copy of the uploaded `csv_data`,
          with no checks or changes to formatting, and no mapped-in VMPs. If a
          codelist has no applicable mapped VMPs, these old downloads are still
          valid
        - "fixed-header" downloads: Downloads that include just the code and
          term/description columns extracted from the original csv_data, with
          from the standardised column headings "code" and "term"
        - "fixed-header plus original code colum": Downloads that include the
          "code" and "term" columns as able, plus an original code column, which
          is just a duplicate of the "code" column with the original column heading,
          to allow existing study code to continue to refer to the same named column
        - "current download": The current default download, which includes the
          code, term, original code columns as above, plus any other original columns
          from the csv_data

        In order to minimise impact on users who may have already downloaded their
        codelist in a previous format, we check the sha provided against all the shas
        of all possible valid downloaded formats.
        """

        # shas already contains one sha, for the current csv data download
        current_csv_data_in_rows = csv_data_to_rows(current_csv_data_download)

        # OLD-STYLE DOWNLOADS
        # valid if we have no VMPs to map in - i.e. our current CSV download has
        # the same number of rows as the original csv_data uploaded to create this
        # version
        if len(current_csv_data_in_rows) == len(self.table):
            old_dmd_download = rows_to_csv_data(self.table)
            shas.append(self.csv_data_sha(old_dmd_download))

        # FIXED HEADER DOWNLOADS
        # CSV downloads that only included the "code" and "term" columns
        # Our current csv data can be just 2 columns wide, if the original
        # CSV data included only a code/term column, and the code column was
        # already called "code". If so, we don't need this check
        if len(current_csv_data_in_rows[0]) > 2:
            fixed_header_data = rows_to_csv_data(
                [row[:2] for row in current_csv_data_in_rows]
            )
            shas.append(self.csv_data_sha(fixed_header_data))

        # FIXED HEADER DOWNLOADS PLUS ORIGINAL CODE COLUMN
        # We now download CSVs with not just the original code column, but also
        # any other original columns (which may include category columns needed
        # in a study)
        # Since previous (valid) downloads may include just code, term
        # and original code column, also allow CSV data that includes just the
        # first 3 columns
        if len(current_csv_data_in_rows[0]) > 3:
            fixed_header_data_with_original_code = rows_to_csv_data(
                [row[:3] for row in current_csv_data_in_rows]
            )
            shas.append(self.csv_data_sha(fixed_header_data_with_original_code))
        return shas

    def csv_data_shas(self):
        """
        Return a list of shas that should all be considered valid when
        checked against the downloaded data in a study repo.

        For non-dm+d codelists, we shoud never need to re-compute these one, as codes don't
        change after a codelist version is moved to under-review (and they can't be downloaded
        when draft).

        For dm+d codelists, we only need to re-compute the shas if the dmd release has changed
        since the last time they were computed.
        """
        if not self.cached_csv_data.get("shas") or (
            self.coding_system_id == "dmd"
            and self.cached_csv_data.get("release") != most_recent_database_alias("dmd")
        ):
            # reset the cache so we refresh any stored dmd data
            self.cached_csv_data = {}

            current_csv_data_download = self.csv_data_for_download()
            shas = [self.csv_data_sha(csv_data=current_csv_data_download)]
            if self.coding_system_id == "dmd":
                shas = self._get_dmd_shas(shas, current_csv_data_download)
            # Re-fetching the CSV data sets the cached data and the release
            # (to the latest (for dm+d) or to the relevant release for this
            # codelist version), so we only need to update the shas now
            self.cached_csv_data.update({"shas": shas})
            self.save()

        return self.cached_csv_data["shas"]

    def formatted_table(self, fixed_headers=False, include_mapped_vmps=False):
        """
        Format the table data for download
        Table data will always include a "code" and "term" column (if it exists in the
        original data) extracted from the original csv data. These may be labelled
        with different headers in the original CSV.

        If fixed_headers=True, return just the code/term columns with the with the standardised headings "code" and "term".

        If fixed_headers=False, we also include an original code column (a duplicate of
        the column labelled "code" but with the heading from the original CSV data), and
        any other columns from the original CSV data.

        include_mapped_vmps: for dm+d codelists, also map in any previous/subsequent
        VMPs
        """

        header_row = [header.lower() for header in self.table[0]]
        # Find the first matching header from the possible code and term column headers for this
        # codelist's coding system.  These are listed in order of assumed most-to-least likely,
        # in case of multiple matching headers
        original_code_header = next(
            header
            for header in self.codelist.coding_system_cls.csv_headers["code"]
            if header in header_row
        )
        original_term_header = next(
            (
                header
                for header in self.codelist.coding_system_cls.csv_headers["term"]
                if header in header_row
            ),
            None,
        )
        # Identify the index for the two columns we want
        code_header_index = header_row.index(original_code_header)
        term_header_index = (
            header_row.index(original_term_header) if original_term_header else None
        )

        table_rows = self.table[1:]
        if include_mapped_vmps and self.coding_system_id == "dmd":
            # ignore include_mapped_vmps if coding system is anything other than dmd
            additional_table_rows = self._get_additional_rows_for_mapped_vmps(
                table_rows, code_header_index, term_header_index
            )
        else:
            additional_table_rows = []

        headers = ["code", "term"]
        code_header_relabelled = original_code_header != "code"

        # Add in any original columns we need to include
        if not fixed_headers:
            if code_header_relabelled:
                # only add in the original code column if it was relabelled (i.e. it
                # wasn't already called "code"
                headers += [header_row[code_header_index]]

            # Include any other original columns as well
            # Other columns in the csv_data may include category column(s). We
            # have no easy way of telling which those are since there's no
            # verification of columns in uploads other than code columns, so if we
            # haven't explicitly requested fixed headers (i.e. this is a dm+d
            # download that's mapping in previous/subsequent VMPs), we just write
            # out all other columns
            other_headers = [
                (i, header)
                for i, header in enumerate(header_row)
                if header and i not in [code_header_index, term_header_index]
            ]
            other_header_ix, other_header_names = (
                list(zip(*other_headers)) if other_headers else [(), ()]
            )
            headers += list(other_header_names)

        # re-write the table data with the new headers, and only the code and term columns
        # plus a duplicate code column with the original column header if required, and
        # any other original columns
        def _csv_row(row, term_ix=None):
            csv_row = [
                row[code_header_index],
                row[term_ix] if term_ix is not None else "",
            ]
            if not fixed_headers:
                if code_header_relabelled:
                    csv_row += [row[code_header_index]]
                csv_row += [row[ix] for ix in list(other_header_ix)]
            return csv_row

        # If there was no original term header, we need to treat the original table data
        # and the additional VMP mapped data differently. The original table data will
        # set the term to an empty string. Additional mapped VMPs will set it to the
        # description generated by the mapping (which will be in the last column of
        # data, if there no original column to map it into)
        table_data = [
            headers,
            *[_csv_row(row, term_ix=term_header_index) for row in table_rows],
        ]
        table_data.extend(
            [
                _csv_row(row, term_ix=term_header_index or -1)
                for row in additional_table_rows
            ],
        )

        return table_data

    def _get_additional_rows_for_mapped_vmps(self, table_rows, code_ix, term_ix):
        """
        Take a list of dm+d table rows for CSV download, plus an index identifying
        which column to find the code and term in for each row, and return a list of
        rows to be added to it with any previous or subsequent mapped VMPs
        """
        term_ix = term_ix or len(self.table[0])
        codes_dict = {row[code_ix]: row for row in table_rows}

        # add in mapped VMP codes
        mapped_vmps_for_this_codelist = vmpprev_full_mappings(codes_dict.keys())

        # mapped_vmps_for_this_codelist is a full list of (vmp, previous) tuples, where one of
        # vmp/previous are in the codelist. It may contain mappings where `previous` is more than
        # one historical step away from `vmp`

        # create a mapping of previous and subsequent VMPs to add, where the
        # keys are the mapped VMPs, and the values are the code(s) in the
        # codelist that they map to/from. Usually there is just a 1:1 mapping, but
        # it's possible that a single VMP could be split and map to 2 new VMPs, or
        # that 2 VMPs could be merged to a single new code.
        previous_vmps_to_add = {}
        subsequent_vmps_to_add = {}

        for vmp, previous in mapped_vmps_for_this_codelist:
            if vmp in codes_dict:
                # mapping in a previous code
                previous_vmps_to_add.setdefault(previous, []).append(vmp)
            else:
                # mapping in a subsequent code
                subsequent_vmps_to_add.setdefault(vmp, []).append(previous)

        assert not set(previous_vmps_to_add) & set(subsequent_vmps_to_add)

        def add_row(vmp, description, original_code):
            # copy the row for the original code that this VMP mapped to,
            # and replace the code and term columns
            # original code is a list, because it's a possibility that a VMP could
            # (although so far hasn't) mapped to more than one code. We just take the
            # first one to get the starting row
            original_code = original_code[0]
            new_row = [*codes_dict[original_code]]
            if len(new_row) == term_ix:
                new_row.append("")
            new_row[code_ix] = vmp
            new_row[term_ix] = description
            return new_row

        additional_rows = []
        # Sort the VMPs being added to ensure consistent order. This will ensure that
        # repeated CSV downloads are the same unless new mapped VMPs are added and
        # can be used to check whether updates to study codelists are required.
        for previous_vmp in sorted(previous_vmps_to_add):
            # add the code to the table data
            # include its description as the code(s) it was superseded by
            # sort the codes so that ordering is consistent between downloads
            original_codes = sorted(previous_vmps_to_add[previous_vmp])
            additional_rows.append(
                add_row(
                    previous_vmp,
                    f"VMP previous to {', '.join(original_codes)}",
                    original_codes,
                )
            )

        for subsequent_vmp in sorted(subsequent_vmps_to_add):
            # add the code to the table data
            # include its description as the code it supersedes
            # sort the codes so that ordering is consistent between downloads
            original_codes = sorted(subsequent_vmps_to_add[subsequent_vmp])
            additional_rows.append(
                add_row(
                    subsequent_vmp,
                    f"VMP subsequent to {', '.join(original_codes)}",
                    original_codes,
                )
            )
        return additional_rows

    def dmd_csv_data_for_download(self, dmd_database_alias=None):
        assert self.coding_system_id == "bnf"
        dmd_coding_system = CODING_SYSTEMS["dmd"].get_by_release_or_most_recent(
            dmd_database_alias
        )
        headers = ["dmd_type", "dmd_id", "dmd_name", "bnf_code"]
        return dict_rows_to_csv_data(headers, bnf_to_dmd(self.codes, dmd_coding_system))

    def download_filename(self):
        if self.codelist_type == "user":
            return f"{self.codelist.user_id}-{self.codelist.slug}-{self.tag_or_hash}"
        else:
            return f"{self.codelist.organisation_id}-{self.codelist.slug}-{self.tag_or_hash}"

    @property
    def is_draft(self):
        return self.status == Status.DRAFT

    @property
    def is_under_review(self):
        return self.status == Status.UNDER_REVIEW

    @property
    def is_published(self):
        return self.status == Status.PUBLISHED


class CachedHierarchy(models.Model):
    """A model to store a JSON representation of a version's hierarchy.

    There is no technical reason why data is not a column on CodelistVersion.  However,
    putting it in a separate table makes it easier to do "select * from
    codelistversion" in a terminal.
    """

    version = models.OneToOneField(
        "CodelistVersion", related_name="cached_hierarchy", on_delete=models.CASCADE
    )
    data = models.TextField()


class CodeObj(models.Model):
    STATUS_CHOICES = [
        ("?", "Undecided"),
        ("!", "In conflict"),
        ("+", "Included with descendants"),
        ("(+)", "Included by ancestor"),
        ("-", "Excluded with descendants"),
        ("(-)", "Excluded by ancestor"),
    ]
    version = models.ForeignKey(
        "CodelistVersion", related_name="code_objs", on_delete=models.CASCADE
    )
    code = models.CharField(max_length=18)
    status = models.CharField(max_length=3, choices=STATUS_CHOICES, default="?")

    class Meta:
        unique_together = ("version", "code")

    def is_included(self):
        return self.status in ["+", "(+)"]

    def is_excluded(self):
        return self.status in ["-", "(-)"]

    def __str__(self):
        return f"{self.code} {self.status}"


class Search(models.Model):
    version = models.ForeignKey(
        "CodelistVersion", related_name="searches", on_delete=models.CASCADE
    )
    # NB, the "term" and "code" max_length and the MinLengthValidator are enforced client-side
    # as well, so if you change the max search length here, remember to change it
    # on the client side as well:
    # assets/src/scripts/components/SearchForm.tsx
    term = models.CharField(
        max_length=255, validators=[MinLengthValidator(3)], null=True, blank=True
    )
    code = models.CharField(
        max_length=18, validators=[MinLengthValidator(1)], null=True, blank=True
    )
    slug = models.SlugField(max_length=255)

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_term_xor_code",
                condition=(
                    models.Q(term__isnull=False, code__isnull=True)
                    | models.Q(code__isnull=False, term__isnull=True)
                ),
            )
        ]

    @property
    def term_or_code(self):
        return self.term or f"code: {self.code}"


class SearchResult(models.Model):
    search = models.ForeignKey(
        "Search", related_name="results", on_delete=models.CASCADE
    )
    code_obj = models.ForeignKey(
        "CodeObj", related_name="results", on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ("search", "code_obj")


class SignOff(models.Model):
    codelist = models.ForeignKey(
        "Codelist", on_delete=models.CASCADE, related_name="signoffs"
    )
    user = models.ForeignKey("opencodelists.User", on_delete=models.CASCADE)
    date = models.DateField()

    class Meta:
        unique_together = [("codelist", "user")]


class Reference(models.Model):
    codelist = models.ForeignKey(
        "Codelist", on_delete=models.CASCADE, related_name="references"
    )
    text = models.CharField(max_length=255)
    url = models.URLField(max_length=1000)

    class Meta:
        unique_together = [("codelist", "url")]


class Collaboration(models.Model):
    codelist = models.ForeignKey(
        "Codelist", on_delete=models.CASCADE, related_name="collaborations"
    )
    collaborator = models.ForeignKey(
        "opencodelists.User", on_delete=models.CASCADE, related_name="collaborations"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
