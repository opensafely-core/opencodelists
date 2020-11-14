from codelists.views import codelist

from ..factories import create_published_version


def test_get(rf):
    clv = create_published_version()
    cl = clv.codelist

    request = rf.get("/")
    response = codelist(request, cl.organisation.slug, cl.slug)

    # check codelist() redirects to the correct version page
    assert response.status_code == 302
    assert (
        response.url == f"/codelist/{cl.organisation.slug}/{cl.slug}/{clv.version_str}/"
    )
