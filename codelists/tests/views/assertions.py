from django.contrib.auth.models import AnonymousUser

from codelists.models import Codelist, CodelistVersion
from opencodelists.models import Organisation
from opencodelists.tests.factories import UserFactory


def assert_unauthenticated(rf, method, view, obj):
    request = getattr(rf, method)("/the/current/url/")
    request.user = AnonymousUser()
    response = view(request, **kwargs_for_obj(obj))
    assert response.status_code == 302
    assert response.url == "/accounts/login/?next=/the/current/url/"


def assert_get_unauthenticated(rf, view, obj):
    assert_unauthenticated(rf, "get", view, obj)


def assert_post_unauthenticated(rf, view, obj):
    assert_unauthenticated(rf, "post", view, obj)


def assert_unauthorised(rf, method, view, obj):
    request = getattr(rf, method)("/the/current/url/")
    request.user = UserFactory()
    response = view(request, **kwargs_for_obj(obj))
    assert response.status_code == 302
    assert response.url == "/"


def assert_get_unauthorised(rf, view, obj):
    assert_unauthorised(rf, "get", view, obj)


def assert_post_unauthorised(rf, view, obj):
    assert_unauthorised(rf, "post", view, obj)


def kwargs_for_obj(obj):
    if isinstance(obj, Organisation):
        return {"organisation_slug": obj.slug}
    elif isinstance(obj, Codelist):
        return {
            "organisation_slug": obj.organisation_id,
            "codelist_slug": obj.slug,
        }
    elif isinstance(obj, CodelistVersion):
        return {
            "organisation_slug": obj.codelist.organisation_id,
            "codelist_slug": obj.codelist.slug,
            "qualified_version_str": obj.qualified_version_str,
        }
    else:
        assert False, type(obj)
