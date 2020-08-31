import string
from datetime import date

import structlog
from django.db import transaction

from opencodelists.models import User

logger = structlog.get_logger()


def create_codelist(
    *,
    project,
    name,
    coding_system_id,
    description,
    methodology,
    csv_data,
    references=None,
    signoffs=None,
):
    """Create a new codelist with a version."""

    with transaction.atomic():
        codelist = project.codelists.create(
            name=name,
            coding_system_id=coding_system_id,
            description=description,
            methodology=methodology,
        )

        create_version(codelist=codelist, csv_data=csv_data)

        if references is not None:
            for reference in references:
                create_reference(codelist=codelist, **reference)

        if signoffs is not None:
            for signoff in signoffs:
                create_signoff(codelist=codelist, **signoff)

    logger.info("Created Codelist", codelist_pk=codelist.pk)

    return codelist


def create_reference(*, codelist, text, url):
    """Create a new Reference for the given Codelist."""
    ref = codelist.references.create(text=text, url=url)

    logger.info("Created Reference", reference_pk=ref.pk, codelist_pk=codelist.pk)

    return ref


def create_signoff(*, codelist, user, date):
    """Create a new SignOff for the given Codelist."""
    user = User.objects.get(username=user)
    signoff = codelist.signoffs.create(user=user, date=date)

    logger.info("Created SignOff", signoff_pk=signoff.pk, codelist_pk=codelist.pk)

    return signoff


@transaction.atomic()
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
            version = codelist.versions.create(
                version_str=version_str, csv_data=csv_data
            )

            logger.info("Created Version", version_pk=version.pk)

            break
    else:
        raise ValueError("E_TOO_MANY_VERSIONS")

    version.definition = version.build_definition()
    version.save()

    return version


@transaction.atomic
def update_codelist(
    *, codelist, project, name, coding_system_id, description, methodology,
):
    """Update a Codelist."""

    codelist.project = project
    codelist.name = name
    codelist.coding_system_id = coding_system_id
    codelist.description = description
    codelist.methodology = methodology

    codelist.save()

    logger.info("Updated Codelist", codelist_pk=codelist.pk)

    return codelist


@transaction.atomic()
def update_version(*, version, csv_data):
    """Update a version."""

    assert version.is_draft
    version.csv_data = csv_data
    version.definition = version.build_definition()
    version.save()

    logger.info("Updated Version", version_pk=version.pk)


def publish_version(*, version):
    """Publish a version."""

    assert version.is_draft
    version.is_draft = False
    version.save()

    logger.info("Published Version", version_pk=version.pk)
    return version
