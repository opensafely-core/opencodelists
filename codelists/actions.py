import csv
from io import StringIO

import structlog
from django.db import transaction
from django.db.models import Q
from django.db.utils import IntegrityError
from django.utils.text import slugify

from builder import actions as builder_actions
from coding_systems.snomedct import ecl_parser
from opencodelists.models import User

from .codeset import Codeset
from .coding_systems import most_recent_database_alias
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
    coding_system_database_alias,
    slug=None,
    references=None,
    signoffs=None,
    tag=None,
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
    create_old_style_version(
        codelist=codelist,
        csv_data=csv_data,
        coding_system_database_alias=coding_system_database_alias,
        tag=tag,
    )
    logger.info("Created Codelist", codelist_pk=codelist.pk)
    return codelist


@transaction.atomic
def create_or_update_codelist(
    *,
    owner,
    name,
    coding_system_id,
    codes,
    coding_system_database_alias,
    slug=None,
    new_slug=None,
    tag=None,
    description=None,
    methodology=None,
    references=None,
    signoffs=None,
    always_create_new_version=False,
    ignore_unfound_codes=False,
    should_publish=False,
):
    slug = slug or slugify(name)
    new_slug = new_slug or slug

    references = references or []
    signoffs = signoffs or []

    try:
        codelist = owner.handles.get(slug=slug).codelist

        update_codelist(
            owner=owner,
            name=name,
            slug=new_slug,
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
            coding_system_database_alias=coding_system_database_alias,
            always_create_new_version=always_create_new_version,
            ignore_unfound_codes=ignore_unfound_codes,
            status=Status.PUBLISHED if should_publish else Status.UNDER_REVIEW,
        )

        return codelist

    except Handle.DoesNotExist:
        return create_codelist_with_codes(
            owner=owner,
            name=name,
            coding_system_id=coding_system_id,
            coding_system_database_alias=coding_system_database_alias,
            codes=codes,
            slug=new_slug,
            tag=tag,
            description=description,
            methodology=methodology,
            references=references,
            signoffs=signoffs,
            status=Status.PUBLISHED,
            ignore_unfound_codes=ignore_unfound_codes,
        )


@transaction.atomic
def create_codelist_with_codes(
    *,
    owner,
    name,
    coding_system_id,
    codes,
    coding_system_database_alias,
    slug=None,
    tag=None,
    description=None,
    methodology=None,
    references=None,
    signoffs=None,
    author=None,
    status=Status.DRAFT,
    ignore_unfound_codes=False,
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
    coding_system = codelist.coding_system_cls.get_by_release(
        coding_system_database_alias
    )
    _create_version_with_codes(
        codelist=codelist,
        codes=codes,
        status=status,
        coding_system_release=coding_system.release,
        tag=tag,
        author=author,
        ignore_unfound_codes=ignore_unfound_codes,
    )
    return codelist


@transaction.atomic
def create_codelist_from_scratch(
    *,
    owner,
    author,  # The User who can edit the draft CodelistVersion
    name,
    coding_system_id,
    coding_system_database_alias,
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
    coding_system = codelist.coding_system_cls.get_by_release(
        coding_system_database_alias
    )
    version = codelist.versions.create(
        author=author,
        status=Status.DRAFT,
        coding_system_release=coding_system.release,
    )
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


def create_old_style_version(
    *, codelist, csv_data, coding_system_database_alias=None, tag=None
):
    coding_system = codelist.coding_system_cls.get_by_release(
        coding_system_database_alias
    )
    if coding_system.has_database:
        # Validate codes against the coding system release we're using to
        # create the version
        code_data = csv.reader(StringIO(csv_data))
        header_row = next(code_data)
        code_header = list({"dmd_id", "code"} & set(header_row))
        assert len(code_header) == 1
        code_col_ix = header_row.index(code_header[0])
        # Find codes
        codes = {row[code_col_ix] for row in code_data}
        assert codes == set(coding_system.lookup_names(codes))

    version = codelist.versions.create(
        csv_data=csv_data,
        status=Status.UNDER_REVIEW,
        coding_system_release=coding_system.release,
        tag=tag,
    )
    cache_hierarchy(version=version)
    logger.info("Created Version", version_pk=version.pk)
    return version


@transaction.atomic
def create_version_with_codes(
    *,
    codelist,
    codes,
    coding_system_database_alias,
    tag=None,
    status=Status.UNDER_REVIEW,
    hierarchy=None,
    codeset=None,
    author=None,
    always_create_new_version=False,
    ignore_unfound_codes=False,
):
    """Create a new version of a codelist with given codes.
    Returns the new version, or None if no version is created because the codes are the
    same as the previous version.
    `hierarchy` and `codeset` may be passed in if they have already been calculated.
    """

    if not codes:
        raise ValueError("No codes")
    prev_clv = codelist.versions.order_by("id").last()
    coding_system = codelist.coding_system_cls.get_by_release(
        coding_system_database_alias
    )
    if always_create_new_version or set(codes) != set(prev_clv.codes):
        return _create_version_with_codes(
            codelist=codelist,
            codes=codes,
            status=status,
            coding_system_release=coding_system.release,
            tag=tag,
            hierarchy=hierarchy,
            codeset=codeset,
            author=author,
            ignore_unfound_codes=ignore_unfound_codes,
        )
    return None


def create_version_from_ecl_expr(
    *, codelist, expr, coding_system_database_alias, tag=None
):
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
    coding_system = codelist.coding_system_cls.get_by_release(
        coding_system_database_alias
    )
    hierarchy = Hierarchy.from_codes(coding_system, codes)

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
        coding_system_database_alias=coding_system.database_alias,
        tag=tag,
        hierarchy=hierarchy,
        codeset=codeset,
    )


def _create_version_with_codes(
    *,
    codelist,
    codes,
    status,
    coding_system_release,
    tag=None,
    hierarchy=None,
    codeset=None,
    author=None,
    ignore_unfound_codes=False,
):
    codes = set(codes)
    coding_system = codelist.coding_system_cls.get_by_release(
        coding_system_release.database_alias
    )
    found_codes = set(coding_system.lookup_names(codes))

    if codes != found_codes:
        if ignore_unfound_codes:
            # This means we're importing (almost certainly bulk importing from the API)
            # and want to (a) ignore codes that aren't in the dictionary, (b) add them
            # to the description so it's transparent
            unfound_codes = codes - found_codes

            if not codelist.description:
                codelist.description = ""
            codelist.description += (
                "\n\nThis codelist was imported automatically. The following codes "
                f"were not found in the {codelist.coding_system_cls.name} dictionary "
                "and so excluded from this codelist: "
                f"{', '.join(unfound_codes)}."
                "\n\nThis may be because this codelist contains both clinical terms and "
                "medications. In which case you may need to create another codelist "
                "for the missing clinical/medication codes."
            )
            codelist.save()
            codes = found_codes
        else:
            raise ValueError(
                f"Attempting to import codes that aren't in the {codelist.coding_system_cls.name}/{coding_system_release.database_alias} coding system: {', '.join(sorted(codes - found_codes))}"
            )

    clv = codelist.versions.create(
        tag=tag,
        status=status,
        author=author,
        coding_system_release=coding_system_release,
    )

    if codeset is None:
        hierarchy = Hierarchy.from_codes(coding_system, codes)
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
        codelist=codelist,
        codes=set(prev_clv.codes),
        status=Status.UNDER_REVIEW,
        coding_system_release=prev_clv.coding_system_release,
    )


@transaction.atomic
def export_to_builder(*, version, author, coding_system_database_alias):
    """Create a new CodelistVersion for editing in the builder."""
    new_coding_system = version.coding_system.get_by_release(
        coding_system_database_alias
    )
    # Create a new CodelistVersion and CodeObjs.
    draft = author.versions.create(
        codelist=version.codelist,
        status=Status.DRAFT,
        coding_system_release=new_coding_system.release,
    )
    CodeObj.objects.bulk_create(
        CodeObj(version=draft, code=code_obj.code, status=code_obj.status)
        for code_obj in version.code_objs.all()
    )

    # Recreate each search using the version specified for the draft coding_system.
    # This creates the SearchResults linked to the new draft.  We
    # can't just copy them across, because the data may have been updated, and new
    # matching concepts might have been imported.
    #
    # In future, we should be able to short-circuit this by checking if the new draft's
    # coding system version is the same as the coding system version on the codelist
    # version that is being exported.
    for search in version.searches.all():
        codes = do_search(draft.coding_system, term=search.term, code=search.code)[
            "all_codes"
        ]
        builder_actions.create_search(
            draft=draft, term=search.term, code=search.code, codes=codes
        )

    # cache hierarchy so we can use the codeset and calculated hierarchy
    cache_hierarchy(version=draft)

    # Find and add any new descendants of codes on the original version. This can
    # occur when the coding system has changed since the original version was
    # created.
    add_new_descendants(version=draft)
    return draft


def add_new_descendants(*, version):
    """
    Find any missing descendant codes on a version and add them.

    The builder frontend cannot deal with a new code if any of its ancestors are included or
    excluded. It CAN deal with a status of ?, as long as the CodeObj exists. New codes that
    are returned as the result of a search will be created as CodeObj instances, with status
    ?, which is fine. However, if a codelist version was created without searches (e.g. via
    the API), there may be new child codes that do not have corresponding CodeObj instances.

    We don't do any status assignment based on whether parent codes are included or excluded,
    we just create the CodeObj, which will by default have a status of ?. These new codes
    will show up in the builder as unresolved, and the user will need to deal with them
    manually.

    See codelists/management/commands/update_draft.py for a mangement
    command that will do the status assignment and report on codes that have been updated.
    """
    current_codes = set(version.codeset.all_codes())
    all_descendants = set(
        child_code
        for (_, child_code) in version.coding_system.descendant_relationships(
            current_codes
        )
    )
    new_descendants = all_descendants - current_codes

    if new_descendants:
        CodeObj.objects.bulk_create(
            [CodeObj(version=version, code=new_code) for new_code in new_descendants]
        )
        # cache hierarchy again after new codes have been added
        cache_hierarchy(version=version)


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


def convert_bnf_codelist_version_to_dmd(version, published=False):
    """
    Convert BNF codelist version to a new dm+d (old-style) codelist.

    Each BNF codelist version is converted to a dm+d codelist with the following attributes:
    - has the same owner (organisation or user) as the original
    - has -dmd appended to the codelist name and slug
    - includes a link to the original codelist version in the methodology
    - has the same description as the original
    - has the same references as the original
    - has "under review" status by default
    - has codes generated by mappings.bnfdmd.mappers.bnf_to_dmd (using the same code as for dmd downloads)

    If there exists a dm+d codelist with this handle already (i.e. a previously converted version),
    a new version is added unless the resultant CodelistVersion is identical to a previous one.
    """
    assert version.coding_system_id == "bnf"
    dmd_csv_data = version.dmd_csv_data_for_download()
    dmd_name = f"{version.codelist.name} - dmd"
    dmd_slug = f"{version.codelist.slug}-dmd"
    dmd_methodology = (
        f"Converted from [pseudo-BNF system codelist]({version.get_absolute_url()})"
    )
    dmd_alias = most_recent_database_alias("dmd")
    dmd_references = [
        {"text": ref.text, "url": ref.url} for ref in version.codelist.references.all()
    ]
    dmd_description = version.codelist.description
    owner = version.codelist.owner

    owner_query = Q(user=owner) if isinstance(owner, User) else Q(organisation=owner)
    existing_handle = Handle.objects.filter(
        owner_query & (Q(name=dmd_name) | Q(slug=dmd_slug))
    ).last()

    if existing_handle:
        for existing_version in existing_handle.codelist.versions.all():
            if existing_version.csv_data == dmd_csv_data.replace("\r", ""):
                raise IntegrityError("Version with identical csv_data exists")
        converted_codelist = create_old_style_version(
            codelist=existing_handle.codelist,
            csv_data=dmd_csv_data,
            coding_system_database_alias=dmd_alias,
        ).codelist

        update_codelist(
            codelist=converted_codelist,
            owner=owner,
            name=dmd_name,
            slug=dmd_slug,
            methodology=dmd_methodology,
            description=dmd_description,
            references=dmd_references,
            signoffs=[
                {"user": signoff.user, "date": signoff.date}
                for signoff in converted_codelist.signoffs.all()
            ],
        )
    else:
        converted_codelist = create_old_style_codelist(
            owner=owner,
            name=dmd_name,
            slug=dmd_slug,
            coding_system_id="dmd",
            coding_system_database_alias=dmd_alias,
            methodology=dmd_methodology,
            description=dmd_description,
            csv_data=dmd_csv_data,
            references=dmd_references,
        )
    if published:
        publish_version(version=converted_codelist.versions.last())
    return converted_codelist
