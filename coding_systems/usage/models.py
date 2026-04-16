"""Generic models for coding system usage data.

Usage data is published separately from the coding system releases, and should
be stored in the main database (not version-specific databases). This allows
usage data to be shared across all versions of a coding system.
"""

from django.db import models


class CodeUsageRelease(models.Model):
    """A published release of usage data for a coding system.

    Each period/year has one release per coding system.
    """

    coding_system = models.CharField(
        max_length=20,
        choices=[
            ("snomedct", "SNOMED CT"),
            ("icd10", "ICD-10"),
            ("opcs4", "OPCS-4"),
        ],
    )
    period = models.CharField(
        max_length=20,
        help_text="Period identifier, e.g. '2023-24' or '2023'",
    )
    source_url = models.URLField(max_length=500)
    imported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("coding_system", "period")
        indexes = [
            models.Index(fields=["coding_system", "period"]),
        ]

    def __str__(self):
        return f"{self.get_coding_system_display()} usage {self.period}"


class CodeUsageEntry(models.Model):
    """A single coding system entry with its usage count for a release.

    Each entry represents how many times a code was used in primary care
    during the period of the release.
    """

    release = models.ForeignKey(CodeUsageRelease, on_delete=models.CASCADE)
    code = models.CharField(
        max_length=18,
        help_text="The code/ID from the coding system (e.g. SNOMED CT concept ID)",
    )
    usage = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ("release", "code")
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["release"]),
        ]

    def __str__(self):
        return f"{self.release.coding_system} {self.code} ({self.usage})"
