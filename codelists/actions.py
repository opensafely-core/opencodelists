import structlog
from django.db import transaction

from opencodelists.models import User

from .definition2 import Definition2
from .hierarchy import Hierarchy
from .models import CodeObj

logger = structlog.get_logger()


def create_codelist(
    *,
    owner,  # Can be an Organisation or a User
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
        codelist = owner.codelists.create(
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


def create_version(*, codelist, csv_data):
    version = codelist.versions.create(csv_data=csv_data)
    logger.info("Created Version", version_pk=version.pk)
    return version


@transaction.atomic
def update_codelist(*, codelist, name, coding_system_id, description, methodology):
    """Update a Codelist."""

    codelist.name = name
    codelist.coding_system_id = coding_system_id
    codelist.description = description
    codelist.methodology = methodology

    codelist.save()

    logger.info("Updated Codelist", codelist_pk=codelist.pk)

    return codelist


def update_version(*, version, csv_data):
    """Update a version."""

    assert version.is_draft
    version.csv_data = csv_data
    version.save()

    logger.info("Updated Version", version_pk=version.pk)


def publish_version(*, version):
    """Publish a version."""

    assert version.is_draft
    version.is_draft = False
    version.save()

    logger.info("Published Version", version_pk=version.pk)

    return version


@transaction.atomic
def convert_codelist_to_new_style(*, codelist):
    """Convert codelist to new style.

    Create a new version with the same codes as the latest version.
    """

    prev_clv = codelist.versions.order_by("id").last()
    assert prev_clv.csv_data is not None
    assert prev_clv.code_objs.count() == 0

    next_clv = codelist.versions.create()

    codes = set(prev_clv.codes)
    hierarchy = Hierarchy.from_codes(codelist.coding_system, codes)
    definition = Definition2.from_codes(codes, hierarchy)

    CodeObj.objects.bulk_create(
        CodeObj(
            version=next_clv,
            code=node,
            status=hierarchy.node_status(
                node, definition.included_ancestors, definition.excluded_ancestors
            ),
        )
        for node in hierarchy.nodes
        if node in codes
    )

    return next_clv
