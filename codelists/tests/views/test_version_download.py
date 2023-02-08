from opencodelists.csv_utils import csv_data_to_rows


def test_get(client, version):
    rsp = client.get(version.get_download_url())
    data = rsp.content.decode("utf8")
    assert data == version.csv_data_for_download()


def test_get_with_fixed_headers(client, old_style_version):
    assert old_style_version.table[0] == ["id", "name"]
    rsp = client.get(old_style_version.get_download_url() + "?fixed-headers")
    data = rsp.content.decode("utf8")
    assert data == old_style_version.csv_data_for_download(fixed_headers=True)
    assert csv_data_to_rows(data)[0] == ["code", "term"]


def test_get_with_fixed_headers_no_matching_term(client, old_style_version):
    old_style_version.csv_data = old_style_version.csv_data.replace(
        "id,name", "id,unk_description"
    )
    old_style_version.save()
    rsp = client.get(old_style_version.get_download_url() + "?fixed-headers")
    data = rsp.content.decode("utf8")
    assert data == old_style_version.csv_data_for_download(fixed_headers=True)
    rows = csv_data_to_rows(data)
    assert rows[0] == ["code", "term"]
    assert {row[1] for row in rows[1:]} == {""}


def test_get_with_fixed_headers_not_downloadable(client, old_style_version):
    old_style_version.csv_data = old_style_version.csv_data.replace(
        "id,name", "unk,name"
    )
    old_style_version.save()
    assert not old_style_version.downloadable
    rsp = client.get(old_style_version.get_download_url() + "?fixed-headers")
    assert rsp.status_code == 400
