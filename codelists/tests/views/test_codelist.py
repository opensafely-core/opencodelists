def test_get(client, codelist):
    latest_version = codelist.latest_version()
    response = client.get(codelist.get_absolute_url())
    assert response.status_code == 302
    if latest_version is None:
        assert response.url == "/"
    else:
        assert response.url == latest_version.get_absolute_url()
