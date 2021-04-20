from functools import wraps

from rest_framework.exceptions import PermissionDenied

from opencodelists.models import Organisation, User

from .models import Codelist, CodelistVersion


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
            raise PermissionDenied

    return wrapped_view
