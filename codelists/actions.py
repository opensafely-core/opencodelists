import structlog
from django.db import transaction
from django.utils.text import slugify

from builder import actions as builder_actions
from coding_systems.snomedct import ecl_parser
from opencodelists.dict_utils import invert_dict
from opencodelists.models import User

from .codeset import Codeset
from .hierarchy import Hierarchy
from .models import Codelist, CodeObj, Status
from .search import do_search

logger = structlog.get_logger()


@transaction.atomic
def create_old_style_codelist(
    *,
    owner,
    name,
    coding_system_id,
    description,
    methodology,
    csv_data,
    slug=None,
    references=None,
    signoffs=None,
):
    """Create a new codelist with an old-style version with given csv_data."""

    codelist = _create_codelist_with_handle(
        owner=owner,
        name=name,
        coding_system_id=coding_system_id,
        description=description,
        methodology=methodology,
        slug=slug,
        references=references,
        signoffs=signoffs,
    )
    create_old_style_version(codelist=codelist, csv_data=csv_data)
    logger.info("Created Codelist", codelist_pk=codelist.pk)
    return codelist


@transaction.atomic
def create_codelist_with_codes(
    *,
    owner,
    name,
    coding_system_id,
    codes,
    slug=None,
    tag=None,
    description=None,
    methodology=None,
    references=None,
    signoffs=None,
):
    """Create a new Codelist with a new-style version with given codes."""

    codelist = _create_codelist_with_handle(
        owner=owner,
        name=name,
        coding_system_id=coding_system_id,
        description=description,
        methodology=methodology,
        slug=slug,
        references=references,
        signoffs=signoffs,
    )
    _create_version_with_codes(
        codelist=codelist, codes=codes, status=Status.PUBLISHED, tag=tag
    )
    return codelist


@transaction.atomic
def create_codelist_from_scratch(
    *,
    owner,
    draft_owner,  # The User who can edit the draft CodelistVersion
    name,
    coding_system_id,
    slug=None,
    tag=None,
    description=None,
    methodology=None,
    references=None,
    signoffs=None,
):
    """Create a new Codelist with a draft new-style version."""

    codelist = _create_codelist_with_handle(
        owner=owner,
        name=name,
        coding_system_id=coding_system_id,
        description=description,
        methodology=methodology,
        slug=slug,
        references=references,
        signoffs=signoffs,
    )
    codelist.versions.create(draft_owner=draft_owner, status=Status.DRAFT)
    return codelist


def _create_codelist_with_handle(
    owner,  # Can be an Organisation or a User
    name,
    coding_system_id,
    description,
    methodology,
    slug=None,
    references=None,
    signoffs=None,
):
    if not slug:
        slug = slugify(name)

    codelist = Codelist.objects.create(
        coding_system_id=coding_system_id,
        description=description,
        methodology=methodology,
    )
    owner.handles.create(codelist=codelist, slug=slug, name=name, is_current=True)

    for reference in references or []:
        codelist.references.create(text=reference["text"], url=reference["url"])

    for signoff in signoffs or []:
        user = User.objects.get(username=signoff["user"])
        signoff = codelist.signoffs.create(user=user, date=signoff["date"])

    return codelist


def create_old_style_version(*, codelist, csv_data):
    version = codelist.versions.create(csv_data=csv_data, status=Status.UNDER_REVIEW)
    logger.info("Created Version", version_pk=version.pk)
    return version


@transaction.atomic
def create_version_with_codes(
    *,
    codelist,
    codes,
    tag=None,
    status=Status.UNDER_REVIEW,
    hierarchy=None,
    codeset=None,
):
    """Create a new version of a codelist with given codes.

    Returns the new version, or None if no version is created because the codes are the
    same as the previous version.  (Future work could allow a force_create parameter.)

    `hierarchy` and `codeset` may be passed in if they have already been calculated.
    """

    if not codes:
        raise ValueError("No codes")

    prev_clv = codelist.versions.order_by("id").last()
    if set(codes) == set(prev_clv.codes):
        return None

    return _create_version_with_codes(
        codelist=codelist,
        codes=codes,
        status=status,
        tag=tag,
        hierarchy=hierarchy,
        codeset=codeset,
    )


def create_version_from_ecl_expr(*, codelist, expr, tag=None):
    """Create a new version of a codelist from given ECL expression.

    Raises ValueError if expression is empty or gives the same as the codelist's
    previous version.
    """

    try:
        parsed_ecl = ecl_parser.handle(expr)
    except ecl_parser.ParseError as e:
        raise ValueError(str(e))

    codes = {item[1] for item in parsed_ecl["included"]} | {
        item[1] for item in parsed_ecl["excluded"]
    }
    hierarchy = Hierarchy.from_codes(codelist.coding_system, codes)

    explicitly_included = set()
    explicitly_excluded = set()

    for operator, code in parsed_ecl["included"]:
        if operator == "<<":
            # code is included with all descendants
            explicitly_included.add(code)
        elif operator == "<":
            # code is not included, but all children are
            for child in hierarchy.child_map.get(code, []):
                explicitly_included.add(child)
        else:
            assert operator is None
            # code is included, but children are not
            explicitly_included.add(code)
            for child in hierarchy.child_map.get(code, []):
                explicitly_excluded.add(child)

    for operator, code in parsed_ecl["excluded"]:
        if operator == "<<":
            # code is excluded with all descendants
            explicitly_excluded.add(code)
        elif operator == "<":
            # code is not excluded, but all children are
            for child in hierarchy.child_map.get(code, []):
                explicitly_excluded.add(child)
        else:
            assert operator is None
            # code is excluded, but children are not
            explicitly_excluded.add(code)
            for child in hierarchy.child_map.get(code, []):
                explicitly_included.add(child)

    codeset = Codeset.from_definition(
        explicitly_included, explicitly_excluded, hierarchy
    )
    return create_version_with_codes(
        codelist=codelist,
        codes=codeset.codes(),
        tag=tag,
        hierarchy=hierarchy,
        codeset=codeset,
    )


def _create_version_with_codes(
    *, codelist, codes, status, tag=None, hierarchy=None, codeset=None
):
    codes = set(codes)
    coding_system = codelist.coding_system
    code_to_term = coding_system.code_to_term(codes)
    assert codes == set(code_to_term)

    clv = codelist.versions.create(tag=tag, status=status)

    if codeset is None:
        hierarchy = Hierarchy.from_codes(codelist.coding_system, codes)
        codeset = Codeset.from_codes(codes, hierarchy)

    CodeObj.objects.bulk_create(
        CodeObj(version=clv, code=code, status=status)
        for code, status in codeset.code_to_status.items()
    )

    return clv


@transaction.atomic
def update_codelist(*, codelist, description, methodology):
    """Update a Codelist."""

    codelist.description = description
    codelist.methodology = methodology

    codelist.save()

    logger.info("Updated Codelist", codelist_pk=codelist.pk)

    return codelist


@transaction.atomic
def publish_version(*, version):
    """Publish a version.

    This deletes all other non-published versions belonging to the codelist.
    """

    assert version.is_under_review
    version.status = Status.PUBLISHED
    version.save()
    version.codelist.versions.exclude(status=Status.PUBLISHED).delete()
    logger.info("Published Version", version_pk=version.pk)


@transaction.atomic
def convert_codelist_to_new_style(*, codelist):
    """Convert codelist to new style.

    Create a new version with the same codes as the latest version.
    """

    prev_clv = codelist.versions.order_by("id").last()
    assert prev_clv.csv_data is not None
    assert prev_clv.code_objs.count() == 0

    return _create_version_with_codes(
        codelist=codelist, codes=set(prev_clv.codes), status=Status.UNDER_REVIEW
    )


@transaction.atomic
def export_to_builder(*, version, owner):
    """Create a new CodelistVersion for editing in the builder."""

    # Create a new CodelistVersion and CodeObjs.
    draft = owner.drafts.create(codelist=version.codelist, status=Status.DRAFT)
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
        codes = do_search(version.coding_system, term=search.term, code=search.code)[
            "all_codes"
        ]
        builder_actions.create_search(
            draft=draft, term=search.term, code=search.code, codes=codes
        )

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


def add_collaborator(*, codelist, collaborator):
    """Add collaborator to codelist."""

    codelist.collaborations.create(collaborator=collaborator)
