from .assertions import assert_post_unauthenticated, assert_post_unauthorised
from .helpers import force_login


def test_post_unauthenticated(client, version_under_review):
    assert_post_unauthenticated(client, version_under_review.get_publish_url())


def test_post_unauthorised(client, version_under_review):
    assert_post_unauthorised(client, version_under_review.get_publish_url())


def test_post_success(client, version_under_review):
    force_login(version_under_review, client)

    response = client.post(version_under_review.get_publish_url())
    version_under_review.refresh_from_db()

    assert response.status_code == 302
    assert response.url == version_under_review.get_absolute_url()
