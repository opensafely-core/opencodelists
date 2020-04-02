from django.db import models
from django.urls import reverse

CODING_SYSTEMS = [
    ("readv2", "Read V2"),
    ("ctv3", "Clinical Terms Version 3 (Read V3)"),
    ("snomedct", "SNOMED CT"),
]


class Publisher(models.Model):
    slug = models.SlugField(primary_key=True)


class Codelist(models.Model):
    publisher = models.ForeignKey(
        "Publisher", related_name="codelists", on_delete=models.CASCADE
    )
    slug = models.SlugField()
    coding_system = models.CharField(choices=CODING_SYSTEMS, max_length=32)

    class Meta:
        unique_together = ("publisher", "slug")

    def get_absolute_url(self):
        return reverse("codelists:codelist", args=(self.publisher_id, self.slug))

    def full_slug(self):
        return "{}/{}".format(self.publisher_id, self.slug)


class CodelistVersion(models.Model):
    codelist = models.ForeignKey(
        "Codelist", related_name="versions", on_delete=models.CASCADE
    )
    version_str = models.CharField(max_length=12)

    class Meta:
        unique_together = ("codelist", "version_str")

    def get_absolute_url(self):
        return self.codelist.get_absolute_url() + "?version=" + self.version_str

    def download_filename(self):
        return "{}-{}-{}-{}".format(
            self.codelist.publisher_id,
            self.codelist.slug,
            self.codelist.coding_system,
            self.version_str,
        )


class CodelistMember(models.Model):
    codelist_version = models.ForeignKey(
        "CodelistVersion", related_name="members", on_delete=models.CASCADE
    )
    code = models.CharField(max_length=18)  # Long enough for a SNOMED code

    class Meta:
        unique_together = ("codelist_version", "code")
