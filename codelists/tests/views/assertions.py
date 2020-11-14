from django.contrib.auth.models import AnonymousUser

from codelists.models import Codelist, CodelistVersion
from opencodelists.models import Organisation


def assert_redirects_to_login_page(rf, method, view, obj):
    if isinstance(obj, Organisation):
        kwargs = {"organisation_slug": obj.slug}
    elif isinstance(obj, Codelist):
        kwargs = {
            "organisation_slug": obj.organisation_id,
            "codelist_slug": obj.slug,
        }
    elif isinstance(obj, CodelistVersion):
        kwargs = {
            "organisation_slug": obj.codelist.organisation_id,
            "codelist_slug": obj.codelist_id,
            "qualified_version_str": obj.qualified_version_str,
        }
    else:
        assert False, type(obj)

    request = getattr(rf, method)("/the/current/url/")
    request.user = AnonymousUser()
    response = view(request, **kwargs)
    assert response.status_code == 302
    assert response.url == "/accounts/login/?next=/the/current/url/"


def assert_get_redirects_to_login_page(rf, view, obj):
    assert_redirects_to_login_page(rf, "get", view, obj)


def assert_post_redirects_to_login_page(rf, view, obj):
    assert_redirects_to_login_page(rf, "post", view, obj)
