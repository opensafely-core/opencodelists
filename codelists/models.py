from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property

from . import coding_system


class Publisher(models.Model):
    slug = models.SlugField(primary_key=True)


class Codelist(models.Model):
    publisher = models.ForeignKey(
        "Publisher", related_name="codelists", on_delete=models.CASCADE
    )
    slug = models.SlugField()
    coding_system_id = models.CharField(
        choices=sorted(coding_system.CODING_SYSTEMS.items()), max_length=32
    )

    class Meta:
        unique_together = ("publisher", "slug")

    @cached_property
    def coding_system(self):
        return coding_system.get(self.coding_system_id)

    def get_absolute_url(self):
        return reverse("codelists:codelist", args=(self.publisher_id, self.slug))

    def full_slug(self):
        return "{}/{}".format(self.publisher_id, self.slug)


class CodelistVersion(models.Model):
    codelist = models.ForeignKey(
        "Codelist", related_name="versions", on_delete=models.CASCADE
    )
    version_str = models.CharField(max_length=12)
    definition = models.TextField()

    class Meta:
        unique_together = ("codelist", "version_str")

    def get_absolute_url(self):
        return self.codelist.get_absolute_url() + "?version=" + self.version_str

    def download_filename(self):
        return "{}-{}-{}-{}".format(
            self.codelist.publisher_id,
            self.codelist.slug,
            self.codelist.coding_system_id,
            self.version_str,
        )

    @cached_property
    def codes(self):
        coding_system = self.codelist.coding_system
        return coding_system.codes_from_query(self.definition)

    @cached_property
    def annotated_codes(self):
        coding_system = self.codelist.coding_system
        return coding_system.annotated_codes(self.codes)
