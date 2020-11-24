from functools import wraps

from django.shortcuts import get_object_or_404

from codelists.models import CodelistVersion
from opencodelists.hash_utils import unhash


def load_draft(view_fn):
    """Load a CodelistVersion (or raise 404) and pass it to view function."""

    @wraps(view_fn)
    def wrapped_view(request, hash, **kwargs):
        id = unhash(hash, "CodelistVersion")
        draft = get_object_or_404(CodelistVersion, id=id)
        return view_fn(request, draft, **kwargs)

    return wrapped_view
