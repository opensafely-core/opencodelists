from functools import wraps

from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect

from opencodelists.hash_utils import unhash
from opencodelists.models import Organisation, User

from ..models import Codelist, CodelistVersion


def load_owner(view_fn):
    """Load an Organisation or User (or raise 404) and pass it to view function.

    Assumes that the view function get a single parameter from the URL:
    organisation_slug/username.
    """

    @wraps(view_fn)
    def wrapped_view(request, organisation_slug=None, username=None):
        if organisation_slug:
            assert not username
            owner = get_object_or_404(Organisation, slug=organisation_slug)
        else:
            assert username
            owner = get_object_or_404(User, username=username)
        return view_fn(request, owner)

    return wrapped_view


def load_codelist(view_fn):
    """Load a Codelist (or raise 404) and pass it to view function.

    Assumes that the view function get a two parameters from the URL:
    organisation_slug/username and codelist_slug.
    """

    @wraps(view_fn)
    def wrapped_view(request, codelist_slug, organisation_slug=None, username=None):
        kwargs = {"slug": codelist_slug}
        if organisation_slug:
            assert not username
            kwargs["organisation_id"] = organisation_slug
        else:
            assert username
            kwargs["user_id"] = username

        cl = get_object_or_404(Codelist, **kwargs)
        return view_fn(request, cl)

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
        query_kwargs = {"codelist__slug": codelist_slug}
        if organisation_slug:
            assert not username
            query_kwargs["codelist__organisation_id"] = organisation_slug
        else:
            assert username
            query_kwargs["codelist__user_id"] = username

        q = Q(tag=tag_or_hash)
        try:
            id = unhash(tag_or_hash, "CodelistVersion")
        except ValueError:
            pass
        else:
            q |= Q(id=id)

        clv = get_object_or_404(CodelistVersion.objects.filter(q), **query_kwargs)

        if clv.draft_owner:
            # TODO test this properly
            return redirect(clv.get_builder_url("draft"))
        else:
            return view_fn(request, clv, **view_kwargs)

    return wrapped_view


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
