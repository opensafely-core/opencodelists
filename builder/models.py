from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property

from codelists.coding_systems import CODING_SYSTEMS
from opencodelists.models import User


class DraftCodelist(models.Model):
    CODING_SYSTEMS_CHOICES = [
        ("snomedct", CODING_SYSTEMS["snomedct"].name),
        ("ctv3", CODING_SYSTEMS["ctv3"].name),
    ]

    owner = models.ForeignKey(
        User, related_name="draft_codelists", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    coding_system_id = models.CharField(
        choices=CODING_SYSTEMS_CHOICES, max_length=32, verbose_name="Coding system"
    )

    class Meta:
        unique_together = ("owner", "slug")

    def __str__(self):
        return self.name

    @cached_property
    def coding_system(self):
        return CODING_SYSTEMS[self.coding_system_id]

    def get_absolute_url(self):
        return reverse("builder:codelist", args=(self.owner.username, self.slug))


class Code(models.Model):
    STATUS_CHOICES = [
        ("?", "Undecided"),
        ("!", "In conflict"),
        ("+", "Included with descendants"),
        ("(+)", "Included by ancestor"),
        ("-", "Excluded with descendants"),
        ("(-)", "Excluded by ancestor"),
    ]
    codelist = models.ForeignKey(
        "DraftCodelist", related_name="codes", on_delete=models.CASCADE
    )
    code = models.CharField(max_length=18)
    status = models.CharField(max_length=3, choices=STATUS_CHOICES, default="?")

    class Meta:
        unique_together = ("codelist", "code")


class Search(models.Model):
    codelist = models.ForeignKey(
        "DraftCodelist", related_name="searches", on_delete=models.CASCADE
    )
    term = models.CharField(max_length=255)
    slug = models.SlugField()

    class Meta:
        unique_together = ("codelist", "slug")

    def get_absolute_url(self):
        return reverse(
            "builder:search",
            args=(self.codelist.owner.username, self.codelist.slug, self.slug),
        )


class SearchResult(models.Model):
    search = models.ForeignKey(
        "Search", related_name="results", on_delete=models.CASCADE
    )
    code = models.ForeignKey("Code", related_name="results", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("search", "code")
