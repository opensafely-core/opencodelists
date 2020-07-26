import string
from datetime import date

from django.db import transaction


def create_codelist(
    *, project, name, coding_system_id, description, methodology, csv_data
):
    """Create a new codelist with a version."""

    with transaction.atomic():
        cl = project.codelists.create(
            name=name,
            coding_system_id=coding_system_id,
            description=description,
            methodology=methodology,
        )
        create_version(codelist=cl, csv_data=csv_data)
    return cl


def create_version(*, codelist, csv_data):
    """Create a new version of a codelist.

    There is a race condition in this code, but in practice we're unlikely to
    hit it.
    """

    base_version_str = str(date.today())
    suffixes = string.ascii_lowercase
    version_strs = [base_version_str] + [f"{base_version_str}-{s}" for s in suffixes]
    for version_str in version_strs:
        if not codelist.versions.filter(version_str=version_str).exists():
            return codelist.versions.create(version_str=version_str, csv_data=csv_data)
    raise ValueError("E_TOO_MANY_VERSIONS")


def update_version(*, version, csv_data):
    """Update a version."""

    assert version.is_draft
    version.csv_data = csv_data
    version.save()


def publish_version(*, version):
    """Publish a version."""

    assert version.is_draft
    version.is_draft = False
    version.save()
