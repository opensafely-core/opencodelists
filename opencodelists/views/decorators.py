from functools import wraps

from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from ..models import Organisation


def load_organisation(view_fn):
    """Load an Organisation (or raise 404) and pass it to view function."""

    @wraps(view_fn)
    def wrapped_view(request, organisation_slug):
        organisation = get_object_or_404(Organisation, slug=organisation_slug)
        return view_fn(request, organisation)

    return wrapped_view


def require_admin_permission(view_fn):
    """Ensure the user is an admin member"""

    @wraps(view_fn)
    def wrapped_view(request, organisation, *args, **kwargs):
        test = lambda user: user.is_admin_member(organisation)  # noqa

        if test(request.user):
            return view_fn(request, organisation, *args, **kwargs)
        else:
            return redirect(reverse("organisations"))

    return wrapped_view
