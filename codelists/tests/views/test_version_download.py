def test_get(client, version):
    rsp = client.get(version.get_download_url())
    data = rsp.content.decode("utf8")
    assert data == version.csv_data_for_download()
