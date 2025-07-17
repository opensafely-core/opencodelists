def test_get(client, bnf_data, bnf_version_asthma):
    rsp = client.get(bnf_version_asthma.get_dmd_download_url())
    data = rsp.text
    assert data == bnf_version_asthma.dmd_csv_data_for_download()
