from functools import wraps

from django.shortcuts import get_object_or_404, redirect

from codelists.models import CodelistVersion
from opencodelists.hash_utils import unhash


def load_draft(view_fn):
    """Load a CodelistVersion (or raise 404) and pass it to view function."""

    @wraps(view_fn)
    def wrapped_view(request, hash, **kwargs):
        id = unhash(hash, "CodelistVersion")
        draft = get_object_or_404(CodelistVersion, id=id)
        if draft.draft_owner:
            return view_fn(request, draft, **kwargs)
        else:
            # TODO test this properly
            return redirect(draft)

    return wrapped_view


def require_permission(view_fn):
    """Ensure the user has permission to edit the draft codelist."""

    @wraps(view_fn)
    def wrapped_view(request, draft):
        if request.user == draft.draft_owner:
            return view_fn(request, draft)
        else:
            return redirect("/")

    return wrapped_view
