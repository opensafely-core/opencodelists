import structlog
from django.db import transaction

from builder import actions as builder_actions
from opencodelists.dict_utils import invert_dict
from opencodelists.models import User

from .definition2 import Definition2
from .hierarchy import Hierarchy
from .models import CodeObj
from .search import do_search

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


@transaction.atomic
def create_codelist_with_codes(*, owner, name, coding_system_id, codes):
    """Create a new Codelist with a CodelistVersion with given codes."""

    codes = set(codes)

    codelist = owner.codelists.create(name=name, coding_system_id=coding_system_id)

    coding_system = codelist.coding_system
    code_to_term = coding_system.code_to_term(codes)
    assert codes == set(code_to_term)

    version = codelist.versions.create()
    hierarchy = Hierarchy.from_codes(codelist.coding_system, codes)
    definition = Definition2.from_codes(codes, hierarchy)

    CodeObj.objects.bulk_create(
        CodeObj(version=version, code=code, status=status)
        for code, status in definition.code_to_status(hierarchy).items()
    )

    return codelist


@transaction.atomic
def create_codelist_from_scratch(*, owner, name, coding_system_id, draft_owner):
    """Create a new Codelist with a draft CodelistVersion."""

    codelist = owner.codelists.create(name=name, coding_system_id=coding_system_id)
    codelist.versions.create(draft_owner=draft_owner)
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
def update_codelist(*, codelist, description, methodology):
    """Update a Codelist."""

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


@transaction.atomic
def convert_codelist_to_new_style(*, codelist):
    """Convert codelist to new style.

    Create a new version with the same codes as the latest version.
    """

    prev_clv = codelist.versions.order_by("id").last()
    assert prev_clv.csv_data is not None
    assert prev_clv.code_objs.count() == 0

    next_clv = codelist.versions.create(is_draft=prev_clv.is_draft)

    codes = set(prev_clv.codes)
    hierarchy = Hierarchy.from_codes(codelist.coding_system, codes)
    definition = Definition2.from_codes(codes, hierarchy)

    CodeObj.objects.bulk_create(
        CodeObj(
            version=next_clv,
            code=node,
            status=hierarchy.node_status(
                node, definition.explicitly_included, definition.explicitly_excluded
            ),
        )
        for node in hierarchy.nodes
        if node in codes
    )

    return next_clv


@transaction.atomic
def export_to_builder(*, version, owner):
    """Create a new CodelistVersion for editing in the builder."""

    # Create a new CodelistVersion and CodeObjs.
    draft = owner.drafts.create(codelist=version.codelist)
    CodeObj.objects.bulk_create(
        CodeObj(version=draft, code=code_obj.code, status=code_obj.status)
        for code_obj in version.code_objs.all()
    )

    # Recreate each search.  This creates the SearchResults linked to the new draft.  We
    # can't just copy them across, because the data may have been updated, and new
    # matching concepts might have been imported.
    #
    # In future, we should be able to short-circuit this by keeping track of the release
    # that version was created with.
    for search in version.searches.all():
        term = search.term
        codes = do_search(version.coding_system, term)["all_codes"]
        builder_actions.create_search(draft=draft, term=term, codes=codes)

    # Update each code status.
    code_to_status = dict(version.code_objs.values_list("code", "status"))
    status_to_code = invert_dict(code_to_status)
    for status, codes in status_to_code.items():
        draft.code_objs.filter(code__in=codes).update(status=status)

    # This assert will fire if new matching concepts have been imported.  At the moment,
    # the builder frontend cannot deal with a CodeObj with status ?  if any of its
    # ancestors are included or excluded.  We will have to deal with this soon but for
    # now fail loudly.
    assert not draft.code_objs.filter(status="?").exists()

    return draft
