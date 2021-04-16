def test_get_for_organisation_owned_codelist(
    client, new_style_codelist, version_with_complete_searches
):
    response = client.get(new_style_codelist.get_absolute_url())
    assert response.status_code == 302
    assert response.url == version_with_complete_searches.get_absolute_url()


def test_get_for_user_owned_codelist(client, user_codelist, user_version):
    response = client.get(user_codelist.get_absolute_url())
    assert response.status_code == 302
    assert response.url == user_version.get_absolute_url()


def test_get_for_new_codelist(client, codelist_from_scratch):
    response = client.get(codelist_from_scratch.get_absolute_url())
    assert response.status_code == 302
    assert response.url == "/"
