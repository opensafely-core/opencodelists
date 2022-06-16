from functools import wraps

from django.shortcuts import get_object_or_404, redirect

from codelists.actions import cache_hierarchy
from codelists.models import CodelistVersion
from opencodelists.hash_utils import unhash


def load_draft(view_fn):
    """Load a CodelistVersion (or raise 404) and pass it to view function."""

    @wraps(view_fn)
    def wrapped_view(request, hash, **kwargs):
        id = unhash(hash, "CodelistVersion")
        version = get_object_or_404(CodelistVersion, id=id)
        if version.is_draft:
            rsp = view_fn(request, version, **kwargs)
            # make sure the draft version has not just been discarded
            if version.exists() and version.hierarchy.dirty:
                cache_hierarchy(version=version)
            return rsp
        else:
            # TODO test this properly
            return redirect(version)

    return wrapped_view


def require_permission(view_fn):
    """Ensure the user has permission to edit the draft codelist."""

    @wraps(view_fn)
    def wrapped_view(request, draft, **kwargs):
        if request.user == draft.author or draft.codelist.can_be_edited_by(
            request.user
        ):
            return view_fn(request, draft, **kwargs)
        else:
            return redirect("/")

    return wrapped_view
