from django.urls import reverse
from pytest_django.asserts import assertContains

from codelists.actions import publish_version

from ..factories import create_draft_version, create_published_version


def test_get_published(client, tennis_elbow_codelist):
    cl = tennis_elbow_codelist
    clv = publish_version(version=cl.versions.first())
    rsp = client.get(clv.get_absolute_url())
    assertContains(rsp, cl.name)
    assertContains(rsp, cl.description)
    assertContains(rsp, cl.methodology)


def test_get_published_with_draft_url(client):
    clv = create_published_version()

    kwargs = dict(
        organisation_slug=clv.codelist.organisation.slug,
        codelist_slug=clv.codelist.slug,
        qualified_version_str=clv.version_str + "-draft",
    )
    url = reverse("codelists:organisation_version", kwargs=kwargs)
    response = client.get(url)

    # check redirect to the non-draft page for a published version
    assert response.status_code == 302
    assert response.url == clv.get_absolute_url()


def test_get_draft(client, tennis_elbow_codelist):
    cl = tennis_elbow_codelist
    clv = cl.versions.first()
    rsp = client.get(clv.get_absolute_url())
    assertContains(rsp, cl.name)
    assertContains(rsp, cl.description)
    assertContains(rsp, cl.methodology)


def test_get_draft_with_published_url(client):
    clv = create_draft_version()
    kwargs = dict(
        organisation_slug=clv.codelist.organisation.slug,
        codelist_slug=clv.codelist.slug,
        qualified_version_str=clv.qualified_version_str[:-6],
    )
    url = reverse("codelists:organisation_version", kwargs=kwargs)
    response = client.get(url)

    # check redirect to the draft page for a draft version
    assert response.status_code == 302
    assert response.url == clv.get_absolute_url()
