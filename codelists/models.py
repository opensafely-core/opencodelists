from django.db import models

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


class CodelistVersion(models.Model):
    codelist = models.ForeignKey(
        "Codelist", related_name="versions", on_delete=models.CASCADE
    )
    version = models.CharField(max_length=12)

    class Meta:
        unique_together = ("codelist", "version")


class CodelistMember(models.Model):
    codelist_version = models.ForeignKey(
        "CodelistVersion", related_name="members", on_delete=models.CASCADE
    )
    value = models.CharField(max_length=18)  # Long enough for a SNOMED code

    class Meta:
        unique_together = ("codelist_version", "value")
