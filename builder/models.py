from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.text import slugify

from codelists.coding_systems import CODING_SYSTEMS
from opencodelists.models import User


class DraftCodelist(models.Model):
    CODING_SYSTEMS_CHOICES = [("snomedct", CODING_SYSTEMS["snomedct"].name)]

    owner = models.ForeignKey(
        User, related_name="draft_codelists", on_delete=models.CASCADE
    )
    name = models.TextField()
    slug = models.SlugField()
    coding_system_id = models.TextField(
        choices=CODING_SYSTEMS_CHOICES, verbose_name="Coding system",
    )

    class Meta:
        unique_together = ("owner", "slug")

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @cached_property
    def coding_system(self):
        return CODING_SYSTEMS[self.coding_system_id]

    def get_absolute_url(self):
        return reverse("builder:codelist", args=(self.owner.username, self.slug))


class Search(models.Model):
    codelist = models.ForeignKey(
        "DraftCodelist", related_name="searches", on_delete=models.CASCADE
    )
    term = models.TextField()
    slug = models.SlugField()

    class Meta:
        unique_together = ("codelist", "slug")

    def save(self, *args, **kwargs):
        self.slug = slugify(self.term)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(
            "builder:search",
            args=(self.codelist.owner.username, self.codelist.slug, self.slug),
        )


class SearchResult(models.Model):
    STATUS_CHOICES = [
        ("?", "Undecided"),
        ("!", "In conflict"),
        # ("+", "Included"),
        ("+<", "Included with descendants"),
        ("(+)", "Included by ancestor"),
        # ("-", "Excluded"),
        ("-<", "Excluded with descendants"),
        ("(-)", "Excluded by ancestor"),
    ]
    search = models.ForeignKey(
        "Search", related_name="results", on_delete=models.CASCADE
    )
    code = models.TextField()
    status = models.TextField(choices=STATUS_CHOICES, default="?")
    matches_term = models.BooleanField()
    is_ancestor = models.BooleanField()
