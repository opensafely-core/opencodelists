import csv
from io import StringIO

from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.text import slugify

from .coding_systems import CODING_SYSTEMS


class Codelist(models.Model):
    CODING_SYSTEMS_CHOICES = sorted(
        (id, system.name) for id, system in CODING_SYSTEMS.items()
    )

    name = models.CharField(max_length=255)
    slug = models.SlugField()
    project = models.ForeignKey(
        "opencodelists.Project", related_name="codelists", on_delete=models.CASCADE
    )
    coding_system_id = models.CharField(
        choices=CODING_SYSTEMS_CHOICES, max_length=32, verbose_name="Coding system",
    )
    version_str = models.CharField(max_length=12, verbose_name="Version")
    description = models.TextField()
    methodology = models.TextField()
    csv_data = models.TextField(verbose_name="CSV data")

    class Meta:
        unique_together = ("project", "slug")

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        self.csv_data = self.csv_data.replace("\r\n", "\n")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @cached_property
    def coding_system(self):
        return CODING_SYSTEMS[self.coding_system_id]

    @cached_property
    def table(self):
        return list(csv.reader(StringIO(self.csv_data)))

    @cached_property
    def codes(self):
        if self.coding_system_id in ["ctv3", "ctv3tpp", "snomedct"]:
            headers, *rows = self.table

            if self.coding_system_id == "snomedct":
                ix = 0
            elif self.slug == "ethnicity":
                ix = 1
            elif "CTV3ID" in headers:
                ix = headers.index("CTV3ID")
            else:
                ix = headers.index("CTV3Code")

            return tuple(sorted({row[ix] for row in rows}))

    def get_absolute_url(self):
        return reverse("codelists:codelist", args=(self.project_id, self.slug))

    def full_slug(self):
        return "{}/{}".format(self.project_id, self.slug)

    def download_filename(self):
        return "{}-{}-{}".format(self.project_id, self.slug, self.version_str)


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
