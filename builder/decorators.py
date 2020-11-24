from functools import wraps

from django.shortcuts import get_object_or_404

from .models import DraftCodelist


def load_codelist(view_fn):
    """Load a DraftCodelist (or raise 404) and pass it to view function."""

    @wraps(view_fn)
    def wrapped_view(request, username, codelist_slug, **kwargs):
        draft = get_object_or_404(DraftCodelist, owner=username, slug=codelist_slug)
        return view_fn(request, draft, **kwargs)

    return wrapped_view
