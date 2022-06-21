import structlog
from django.core.cache import cache
from django.db import transaction
from django.db.utils import IntegrityError
from django.utils.text import slugify

from builder import actions as builder_actions
from coding_systems.snomedct import ecl_parser
from opencodelists.models import User

from .codeset import Codeset
from .hierarchy import Hierarchy
from .models import CachedHierarchy, Codelist, CodeObj, Handle, Status
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
def create_or_update_codelist(
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
    slug = slug or slugify(name)
    references = references or []
    signoffs = signoffs or []

    try:
        codelist = owner.handles.get(slug=slug).codelist

        update_codelist(
            owner=owner,
            name=name,
            slug=slug,
            codelist=codelist,
            description=description,
            methodology=methodology,
            references=references,
            signoffs=signoffs,
        )
        create_version_with_codes(
            codelist=codelist,
            codes=codes,
            tag=tag,
        )

        return codelist

    except Handle.DoesNotExist:
        return create_codelist_with_codes(
            owner=owner,
            name=name,
            coding_system_id=coding_system_id,
            codes=codes,
            slug=slug,
            tag=tag,
            description=description,
            methodology=methodology,
            references=references,
            signoffs=signoffs,
        )


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
    author=None,
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
        codelist=codelist, codes=codes, status=Status.PUBLISHED, tag=tag, author=author
    )
    return codelist


@transaction.atomic
def create_codelist_from_scratch(
    *,
    owner,
    author,  # The User who can edit the draft CodelistVersion
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
    version = codelist.versions.create(author=author, status=Status.DRAFT)
    cache_hierarchy(version=version)
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
    cache_hierarchy(version=version)
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
    author=None,
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
        author=author,
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
    *, codelist, codes, status, tag=None, hierarchy=None, codeset=None, author=None
):
    codes = set(codes)
    coding_system = codelist.coding_system
    code_to_term = coding_system.code_to_term(codes)
    assert codes == set(code_to_term)

    clv = codelist.versions.create(tag=tag, status=status, author=author)

    if codeset is None:
        hierarchy = Hierarchy.from_codes(codelist.coding_system, codes)
        codeset = Codeset.from_codes(codes, hierarchy)

    CodeObj.objects.bulk_create(
        CodeObj(version=clv, code=code, status=status)
        for code, status in codeset.code_to_status.items()
    )

    cache_hierarchy(version=clv, hierarchy=hierarchy)

    return clv


@transaction.atomic
def update_codelist(
    *, codelist, owner, name, slug, description, methodology, references, signoffs
):
    """Update a Codelist.

        codelist: the codelist to update
        description: the codelist's description
        description: the codelist's methodology
        references: a list of dicts with keys `text` and `url`
        signoffs: a list of dicts with keys `user` and `date`

    Any existing references or signoffs not provided in parameters will be deleted.
    Other references or signoffs will be created or updated as necessary.
    """

    current_handle = codelist.current_handle
    if (
        current_handle.owner != owner
        or current_handle.name != name
        or current_handle.slug != slug
    ):
        try:
            handle, created = owner.handles.get_or_create(
                codelist=codelist,
                slug=slug,
                defaults={"name": name, "is_current": True},
            )
        except IntegrityError as e:
            assert "UNIQUE constraint failed" in str(e)

            # The extra error handling here and below is necessary because when
            # an IntegrityError is raised, we cannot tell whether the
            # IntegrityError was caused by a duplicate slug or by a duplicate
            # name.
            #
            # Specifically, consider two existing handles for different
            # codelists belonging to the same owner:
            #
            #  * h1 = Handle(owner=O, codelist=C1, name="n1", slug="s1")
            #  * h2 = Handle(owner=O, codelist=C2, name="n2", slug="s2")
            #
            # If a user tries to change h1's slug to "s2", then the above
            # get_or_create will create a new handle, h3:
            #
            #  * h3 = Handle(owner=O, codelist=C1, name="n1", slug="s2")
            #
            # There will now be two handles with the same name ("n1") and two
            # with the same slug ("s2").  So both of the unique_together
            # constraints are violated, but we are only notified about one,
            # chosen apparently non-deterministically.
            #
            # If the get_or_create() above raises an IntegrityError, then it
            # will be because the user is trying to reuse a slug.
            #
            # If the save() below raises an IntegrityError, then it will be
            # because the user is trying to reuse a name.
            raise DuplicateHandleError("slug")

        if not created:
            handle.name = name
            handle.is_current = True
            try:
                handle.save()
            except IntegrityError as e:
                # See comment above.
                assert "UNIQUE constraint failed" in str(e)
                raise DuplicateHandleError("name")

        codelist.handles.exclude(pk=handle.pk).update(is_current=False)
        # current_handle is a cached property, so we want to clear it when it changes.
        del codelist.current_handle

    codelist.description = description
    codelist.methodology = methodology
    codelist.save()

    existing_reference_urls = {reference.url for reference in codelist.references.all()}
    updated_reference_urls = {reference["url"] for reference in references}

    for url in existing_reference_urls - updated_reference_urls:
        codelist.references.get(url=url).delete()

    for reference in references:
        codelist.references.update_or_create(url=reference["url"], defaults=reference)

    existing_signoff_users = {signoff.user for signoff in codelist.signoffs.all()}
    updated_signoff_users = {signoff["user"] for signoff in signoffs}

    for user in existing_signoff_users - updated_signoff_users:
        codelist.signoffs.get(user=user).delete()

    for signoff in signoffs:
        codelist.signoffs.update_or_create(user=signoff["user"], defaults=signoff)

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
def delete_version(*, version):
    """Delete a version.

    If this is the only version, the codelist will also be deleted.

    Returns a boolean indicating whether the codelist was deleted.
    """

    assert version.is_under_review
    codelist = version.codelist
    if codelist.versions.count() == 1:
        codelist.delete()
        logger.info(
            "Deleted Version and Codelist",
            codelist_pk=codelist.pk,
            version_pk=version.pk,
        )
        # We clear the pk so that we can check (eg in the load_version decorator)
        # whether the version is still in the database.
        version.pk = None
        return True
    else:
        version.delete()
        logger.info("Deleted Version", version_pk=version.pk)
        return False


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
def export_to_builder(*, version, author):
    """Create a new CodelistVersion for editing in the builder."""

    # Create a new CodelistVersion and CodeObjs.
    draft = author.versions.create(codelist=version.codelist, status=Status.DRAFT)
    CodeObj.objects.bulk_create(
        CodeObj(version=draft, code=code_obj.code, status=code_obj.status)
        for code_obj in version.code_objs.all()
    )
    draft, _ = update_draft(draft=draft, source_version=version)
    return draft


def update_draft(*, draft, source_version=None):
    """
    Update this draft version in case data have been updated, by:
    1) recreating the searches, either using the searches from a source version
       (for a new draft created by `export_to_builder`), or from the searches
       already on the draft
    2) checking for any new codes and ensuring the codeset is up to date

    This is called on every GET for a draft, since we can't (currently) tell if the
    version of a coding system used to create the draft initially is the current one.
    However, coding systems don't get updated very frequently, so we cache that we've
    checked it, so we don't have to redo it every time.
    """
    cached_updates = cache.get("updated_drafts", [])
    updates = {}
    if draft.pk not in cached_updates:
        _recreate_draft_searches(source_version or draft, draft)
        updates = _check_new_concepts(draft)
        cached_updates.append(draft.pk)
        # cache for 24 hrs
        cache.set("updated_drafts", cached_updates, timeout=60 * 60 * 24)
    return draft, updates


def _recreate_draft_searches(source_version, draft):
    """
    Recreate each search.  This creates the SearchResults linked to the new/updated draft.  We
    can't just copy them across, because the data may have been updated, and new
    matching concepts might have been imported.
    In future, we should be able to short-circuit this by keeping track of the release
    that version was created with.
    """
    for search in source_version.searches.all():
        codes = do_search(
            source_version.coding_system, term=search.term, code=search.code
        )["all_codes"]
        builder_actions.create_or_update_search(
            draft=draft, term=search.term, code=search.code, codes=codes
        )
    cache_hierarchy(version=draft)


def _check_new_concepts(draft):
    """
    Check for new matching concepts and ensure the codeset is up to date so the
    builder frontend can display it

    The recreated search will add any new concepts that are returned by a search.
    The builder frontend can't deal with any new concepts (with unresolved status)
    if they have a parent that is included/excluded.

    Update all code statuses with the known statuses that are explicitly included
    or excluded.  This will assign statuses to unresolved codes that have included/excluded
    parents.  It will also update any previously implicitly included/excluded status that
    are no longer applicable.

    e.g. On the initial draft, B inherited from A;
     - A was explicitly included, so B was implicitly included
    After a coding system update, now A and B have swapped, so A inherits from B
     - A is still explicitly included
     - B is now unresolved as it has no parents that are explicitly included or
       excluded (the fronted can deal with that)
    """
    # Make a copy of the pre-update code status; this will contain all codes returned
    # by the recreated searches.  New codes will have status "?" at this stage, and
    # any old codes will still be on the draft
    initial_statuses = {**draft.codeset.code_to_status}

    # if there are any code objs on the draft that are no longer in the coding system,
    # delete them
    draft_codes = set(draft.code_objs.values_list("code", flat=True))
    codes_in_coding_system = set(draft.coding_system.code_to_term(draft_codes))
    old_codes = draft_codes - codes_in_coding_system
    if old_codes:
        CodeObj.objects.filter(version=draft, code__in=old_codes).delete()
        logger.info(
            "Old codes no longer in coding system removed from draft",
            draft=draft,
            coding_system=draft.coding_system,
            removed_codes=old_codes,
        )

    # Update the code statuses again for the explicitly included/excluded codes, and
    # reset any implicit statuses
    explicitly_included_or_excluded = {
        (code, "+") for code in draft.codeset.codes("+")
    } | {(code, "-") for code in draft.codeset.codes("-")}
    builder_actions.update_code_statuses(
        draft=draft, updates=explicitly_included_or_excluded, reset=True
    )

    # return a dict of new, removed and changed codes
    all_changes = set(draft.codeset.code_to_status.items()) - set(
        initial_statuses.items()
    )
    new_code_statuses = {
        (code, status)
        for code, status in draft.codeset.code_to_status.items()
        if initial_statuses[code] == "?"
    }
    changed_code_statuses = all_changes - new_code_statuses
    return {
        "added": new_code_statuses,
        "changed": changed_code_statuses,
        "removed": old_codes,
    }


def add_collaborator(*, codelist, collaborator):
    """Add collaborator to codelist."""

    codelist.collaborations.create(collaborator=collaborator)


def cache_hierarchy(*, version, hierarchy=None):
    """Cache the version's hierarchy.

    This should be called by every action that creates a version or updates a version's
    hierarchy.
    """

    if not version.has_hierarchy:
        return
    if hierarchy is None:
        hierarchy = version.calculate_hierarchy()
    cached_hierarchy, _ = CachedHierarchy.objects.get_or_create(version=version)
    cached_hierarchy.data = hierarchy.data_for_cache()
    cached_hierarchy.save()


def add_codelist_tag(*, codelist, tag):
    codelist.tags.add(tag)


class DuplicateHandleError(IntegrityError):
    """Indicates an attempt to save a Handle whose slug or name duplicates that
    of another Handle with the same owner.

    See comment block in update_codelist for details of why this is necessary.
    """

    def __init__(self, field):
        self.field = field
