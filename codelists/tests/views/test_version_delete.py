from .assertions import assert_post_unauthenticated, assert_post_unauthorised
from .helpers import force_login


def test_post_unauthenticated(client, version):
    assert_post_unauthenticated(client, version.get_publish_url())


def test_post_unauthorised(client, version):
    assert_post_unauthorised(client, version.get_publish_url())


def test_post_success(client, old_style_codelist):
    codelist = old_style_codelist
    version1, version2 = codelist.versions.order_by("id")
    force_login(codelist, client)

    response = client.post(version2.get_delete_url())
    assert response.status_code == 302
    assert response.url == codelist.get_absolute_url()

    response = client.post(version1.get_delete_url())
    assert response.status_code == 302
    assert response.url == "/"
