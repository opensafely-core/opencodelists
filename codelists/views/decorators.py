from functools import wraps

from django.db import OperationalError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect

from opencodelists.hash_utils import unhash
from opencodelists.models import Organisation, User

from ..actions import cache_hierarchy
from ..models import Codelist, CodelistVersion


def load_owner(view_fn):
    """Load an Organisation or User (or raise 404) and pass it to view function.

    Assumes that the view function get a single parameter from the URL:
    organisation_slug/username.
    """

    @wraps(view_fn)
    def wrapped_view(request, organisation_slug=None, username=None):
        owner = _load_owner_or_404(organisation_slug, username)
        return view_fn(request, owner)

    return wrapped_view


def load_codelist(view_fn):
    """Load a Codelist (or raise 404) and pass it to view function.

    Assumes that the view function get a two parameters from the URL:
    organisation_slug/username and codelist_slug.
    """

    @wraps(view_fn)
    def wrapped_view(request, codelist_slug, organisation_slug=None, username=None):
        owner = _load_owner_or_404(organisation_slug, username)
        codelist = _load_codelist_or_404(owner, codelist_slug)
        return view_fn(request, codelist)

    return wrapped_view


def load_version(view_fn):
    """Load a CodelistVersion (or raise 404) and pass it to view function.

    Assumes that the view function get a three parameters from the URL,
    organisation_slug/username, codelist_slug, and identifier:
    """

    @wraps(view_fn)
    def wrapped_view(
        request,
        codelist_slug,
        tag_or_hash,
        organisation_slug=None,
        username=None,
        **view_kwargs,
    ):
        owner = _load_owner_or_404(organisation_slug, username)
        codelist = _load_codelist_or_404(owner, codelist_slug)
        version = _load_version_or_404(codelist, tag_or_hash)

        try:
            if version.is_draft:
                return redirect(version.get_builder_draft_url())
            else:
                if version.pk and (
                    not hasattr(version, "cached_hierarchy")
                    or (version.has_hierarchy and version.hierarchy.dirty)
                ):
                    cache_hierarchy(version=version)
                rsp = view_fn(request, version, **view_kwargs)
                return rsp
        except OperationalError as e:
            # In dev mode if you try and view a codelist from a coding_system release
            # that is not available locally, you get an unhelpful message like:
            # "no such table: dmd_amp".
            # This intercepts those messages, and adds a helpful message telling you
            # which database is likely missing.
            if "no such table" in str(e):
                missing_db = f"{version.coding_system.database_alias}.sqlite3"
                missing_db_dir = f"coding_systems/{version.coding_system.id}/"
                raise type(e)(
                    f"{str(e)}\n\n"
                    f"If this is development then you may be missing the following sqlite database:\n\n"
                    f"- {missing_db_dir}{missing_db}\n\n"
                    f'NB the "missing" database will likely appear under {missing_db_dir} but if so it\'s probably empty and needs replacing with the real version copied from production.'
                ) from e
            raise

    return wrapped_view


def _load_owner_or_404(organisation_slug=None, username=None):
    if organisation_slug:
        assert not username
        return get_object_or_404(Organisation, slug=organisation_slug)
    else:
        assert username
        return get_object_or_404(User, username=username)


def _load_codelist_or_404(owner, codelist_slug):
    handle = get_object_or_404(owner.handles, slug=codelist_slug)
    return handle.codelist


def _load_version_or_404(codelist, tag_or_hash):
    q = Q(tag=tag_or_hash)
    try:
        id = unhash(tag_or_hash, "CodelistVersion")
    except ValueError:
        pass
    else:
        q |= Q(id=id)

    return get_object_or_404(codelist.versions.filter(q))


def require_permission(view_fn):
    """Ensure the user has permission to access the view."""

    @wraps(view_fn)
    def wrapped_view(request, obj, *args, **kwargs):
        if isinstance(obj, CodelistVersion):
            test = obj.codelist.can_be_edited_by
        elif isinstance(obj, Codelist):
            test = obj.can_be_edited_by
        elif isinstance(obj, User):
            test = lambda user: user == obj  # noqa
        elif isinstance(obj, Organisation):
            test = lambda user: user.is_member(obj)  # noqa
        else:
            assert False, obj

        if test(request.user):
            return view_fn(request, obj, *args, **kwargs)
        else:
            return redirect("/")

    return wrapped_view
