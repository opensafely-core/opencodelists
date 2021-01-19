from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property

from mappings.bnfdmd.mappers import bnf_to_dmd
from opencodelists.csv_utils import (
    csv_data_to_rows,
    dict_rows_to_csv_data,
    rows_to_csv_data,
)
from opencodelists.hash_utils import hash, unhash

from .coding_systems import CODING_SYSTEMS
from .presenters import present_definition_for_download


class Codelist(models.Model):
    CODING_SYSTEMS_CHOICES = sorted(
        (id, system.name) for id, system in CODING_SYSTEMS.items()
    )

    name = models.CharField(max_length=255)
    slug = models.SlugField()
    organisation = models.ForeignKey(
        "opencodelists.Organisation",
        null=True,
        related_name="codelists",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        "opencodelists.User",
        null=True,
        related_name="codelists",
        on_delete=models.CASCADE,
    )
    coding_system_id = models.CharField(
        choices=CODING_SYSTEMS_CHOICES, max_length=32, verbose_name="Coding system"
    )
    description = models.TextField(null=True, blank=True)
    methodology = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("organisation", "name", "slug"), ("user", "name", "slug")]
        constraints = [
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_organisation_xor_user",
                check=(
                    models.Q(organisation_id__isnull=False, user_id__isnull=True)
                    | models.Q(user_id__isnull=False, organisation_id__isnull=True)
                ),
            )
        ]

    def __str__(self):
        return self.name

    @cached_property
    def coding_system(self):
        return CODING_SYSTEMS[self.coding_system_id]

    @property
    def codelist_type(self):
        if self.user_id:
            assert not self.organisation_id
            return "user"
        else:
            assert self.organisation_id
            return "organisation"

    def get_absolute_url(self):
        return reverse(
            f"codelists:{self.codelist_type}_codelist", kwargs=self.url_kwargs
        )

    def get_update_url(self):
        return reverse(
            f"codelists:{self.codelist_type}_codelist_update", kwargs=self.url_kwargs
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
            return "{}/{}".format(self.organisation_id, self.slug)
        else:
            return "user/{}/{}".format(self.user_id, self.slug)

    def is_new_style(self):
        return self.versions.filter(csv_data__isnull=True).exists()


class CodelistVersion(models.Model):
    codelist = models.ForeignKey(
        "Codelist", on_delete=models.CASCADE, related_name="versions"
    )
    # If set, indicates that a CodelistVersion is a draft that's being edited in the
    # builder.
    draft_owner = models.ForeignKey(
        "opencodelists.User", related_name="drafts", on_delete=models.CASCADE, null=True
    )
    tag = models.CharField(max_length=12, null=True)
    csv_data = models.TextField(verbose_name="CSV data", null=True)
    # This field indicates whether a CodelistVersion is published or not.  This doesn't
    # have much practical meaning at the moment and should be revisited.
    is_draft = models.BooleanField(default=True)

    # Indicates whether a CodelistVersion was edited in the builder, and then discarded.
    discarded = models.BooleanField(default=False)

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

    def get_create_url(self):
        return reverse(
            f"codelists:{self.codelist_type}_version_create", kwargs=self.url_kwargs
        )

    def get_builder_url(self, view_name, *args):
        return reverse(f"builder:{view_name}", args=[self.hash] + list(args))

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
        return CODING_SYSTEMS[self.coding_system_id]

    @property
    def codelist_type(self):
        return self.codelist.codelist_type

    @cached_property
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

    @cached_property
    def all_related_codes(self):
        if self.csv_data:
            return self._old_style_codes()
        else:
            return self.code_objs.values_list("code", flat=True)

    @cached_property
    def codes(self):
        if self.csv_data:
            return self._old_style_codes()
        else:
            return self._new_style_codes()

    def _old_style_codes(self):
        if self.coding_system_id in ["ctv3", "ctv3tpp", "snomedct"]:
            headers, *rows = self.table

            for header in ["CTV3ID", "CTV3Code", "ctv3_id", "snomedct_id", "id"]:
                if header in headers:
                    ix = headers.index(header)
                    break
            else:
                if self.codelist.slug == "ethnicity":
                    ix = 1
                else:
                    ix = 0

            return tuple(sorted({row[ix] for row in rows}))

    @property
    def in_progress(self):
        return self.draft_owner

    def _new_style_codes(self):
        return tuple(
            sorted(
                self.code_objs.filter(status__in=["+", "(+)"]).values_list(
                    "code", flat=True
                )
            )
        )

    def csv_data_for_download(self):
        if self.csv_data:
            return self.csv_data
        return rows_to_csv_data(self.table)

    def definition_csv_data_for_download(self):
        return rows_to_csv_data(present_definition_for_download(self))

    def dmd_csv_data_for_download(self):
        assert self.coding_system_id == "bnf"
        headers = ["dmd_type", "dmd_id", "dmd_name", "bnf_code"]
        return dict_rows_to_csv_data(headers, bnf_to_dmd(self.codes))

    def download_filename(self):
        if self.codelist_type == "user":
            return "{}-{}-{}".format(
                self.codelist.user_id, self.codelist.slug, self.tag_or_hash
            )
        else:
            return "{}-{}-{}".format(
                self.codelist.organisation_id, self.codelist.slug, self.tag_or_hash
            )

    def can_be_edited_by(self, user):
        if self.codelist_type == "user":
            return user == self.user
        else:
            return user.is_member(self.organisation)


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


class Search(models.Model):
    version = models.ForeignKey(
        "CodelistVersion", related_name="searches", on_delete=models.CASCADE
    )
    term = models.CharField(max_length=255)
    slug = models.SlugField()

    class Meta:
        unique_together = ("version", "slug")


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


class Reference(models.Model):
    codelist = models.ForeignKey(
        "Codelist", on_delete=models.CASCADE, related_name="references"
    )
    text = models.CharField(max_length=255)
    url = models.URLField()
