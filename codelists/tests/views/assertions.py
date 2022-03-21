from opencodelists.models import User


def assert_unauthenticated(client, method, url):
    response = getattr(client, method)(url)
    assert (
        response.status_code == 302
    ), f"Unexpected status code!  Can unauthenticated user {method.upper()} to {url}?"
    assert response.url.startswith("/accounts/login/")


def assert_get_unauthenticated(client, url):
    assert_unauthenticated(client, "get", url)


def assert_post_unauthenticated(client, url):
    assert_unauthenticated(client, "post", url)


def assert_unauthorised(client, method, url):
    user = User.objects.create_user(
        username="ursula", password="test", email="ursula@test.ac.uk", name="Ursula"
    )
    client.force_login(user)
    response = getattr(client, method)(url)
    assert (
        response.status_code == 302
    ), f"Unexpected status code!  Can unauthorised user {method.upper()} to to {url}?"
    assert response.url == "/"


def assert_get_unauthorised(client, url):
    assert_unauthorised(client, "get", url)


def assert_post_unauthorised(client, url):
    assert_unauthorised(client, "post", url)
