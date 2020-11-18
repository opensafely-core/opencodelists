from pytest_django.asserts import assertContains

from codelists.actions import publish_version

from ..factories import create_published_version_for_user


def test_get(client, tennis_elbow_codelist):
    cl = tennis_elbow_codelist
    clv = publish_version(version=cl.versions.first())
    rsp = client.get(clv.get_absolute_url())
    assertContains(rsp, cl.name)
    assertContains(rsp, cl.description)
    assertContains(rsp, cl.methodology)


def test_get_for_user(client):
    clv = create_published_version_for_user()
    response = client.get(clv.get_absolute_url())
    assert response.status_code == 200
