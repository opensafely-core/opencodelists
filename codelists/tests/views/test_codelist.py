from ..factories import create_published_version, create_published_version_for_user


def test_get_for_organisation(client):
    clv = create_published_version()
    cl = clv.codelist

    response = client.get(cl.get_absolute_url())

    # check redirect to the correct version page
    assert response.status_code == 302
    assert response.url == clv.get_absolute_url()


def test_get_for_user(client):
    clv = create_published_version_for_user()
    cl = clv.codelist

    response = client.get(cl.get_absolute_url())

    # check redirect to the correct version page
    assert response.status_code == 302
    assert response.url == clv.get_absolute_url()
