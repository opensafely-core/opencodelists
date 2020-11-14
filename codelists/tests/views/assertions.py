from django.contrib.auth.models import AnonymousUser


def assert_redirects_to_login_page(rf, method, view, **kwargs):
    request = getattr(rf, method)("/the/current/url/")
    request.user = AnonymousUser()
    response = view(request, **kwargs)
    assert response.status_code == 302
    assert response.url == "/accounts/login/?next=/the/current/url/"


def assert_get_redirects_to_login_page(rf, view, **kwargs):
    assert_redirects_to_login_page(rf, "get", view, **kwargs)


def assert_post_redirects_to_login_page(rf, view, **kwargs):
    assert_redirects_to_login_page(rf, "post", view, **kwargs)
