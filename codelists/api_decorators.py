from functools import wraps

from django.http import JsonResponse
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

from opencodelists.models import Organisation, User

from .models import Codelist, CodelistVersion


def require_authentication(view_fn):
    """Ensure the user has supplied an active token."""

    @wraps(view_fn)
    def wrapped_view(request, *args, **kwargs):
        try:
            authenticate(request)
        except AuthenticationFailed as e:
            return JsonResponse(
                {"error": "Unauthenticated", "details": str(e)}, status=401
            )

        return view_fn(request, *args, **kwargs)

    return wrapped_view


def authenticate(request):
    authentication = TokenAuthentication()
    result = authentication.authenticate(request)
    if result is None:
        raise AuthenticationFailed("No token header provided.")
    request.user = result[0]


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
            return JsonResponse({"error": "Unauthorised"}, status=403)

    return wrapped_view
