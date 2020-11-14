from pytest_django.asserts import assertContains

from codelists.actions import publish_version
from codelists.views import version

from ..factories import create_draft_version, create_published_version


def test_version(client, tennis_elbow_codelist):
    cl = tennis_elbow_codelist
    clv = publish_version(version=cl.versions.first())
    rsp = client.get(f"/codelist/{cl.organisation.slug}/{cl.slug}/{clv.version_str}/")
    assertContains(rsp, cl.name)
    assertContains(rsp, cl.description)
    assertContains(rsp, cl.methodology)


def test_version_redirects(rf):
    clv = create_published_version()
    cl = clv.codelist
    request = rf.get("/")
    response = version(
        request, cl.organisation.slug, cl.slug, f"{clv.version_str}-draft"
    )

    # check version() redirects to the non-draft page for a published version
    assert response.status_code == 302
    assert (
        response.url == f"/codelist/{cl.organisation.slug}/{cl.slug}/{clv.version_str}/"
    )


def test_draft_version(client, tennis_elbow_codelist):
    cl = tennis_elbow_codelist
    clv = cl.versions.first()
    rsp = client.get(
        f"/codelist/{cl.organisation.slug}/{cl.slug}/{clv.version_str}-draft/"
    )
    assertContains(rsp, cl.name)
    assertContains(rsp, cl.description)
    assertContains(rsp, cl.methodology)


def test_draft_version_redirects(rf):
    clv = create_draft_version()
    cl = clv.codelist
    request = rf.get("/")
    response = version(request, cl.organisation.slug, cl.slug, clv.version_str)

    # check version() redirects to the draft page for a draft version
    assert response.status_code == 302

    expected = f"/codelist/{cl.organisation.slug}/{cl.slug}/{clv.version_str}-draft/"
    assert response.url == expected
