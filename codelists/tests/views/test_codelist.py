from ..factories import create_published_version


def test_get(client):
    clv = create_published_version()
    cl = clv.codelist

    response = client.get(cl.get_absolute_url())

    # check redirect to the correct version page
    assert response.status_code == 302
    assert response.url == clv.get_absolute_url()
