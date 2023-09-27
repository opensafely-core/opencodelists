from mappings.dmdvmpprevmap.models import Mapping
from opencodelists.csv_utils import csv_data_to_rows


def test_get(client, version):
    rsp = client.get(version.get_download_url())
    data = rsp.content.decode("utf8")
    assert data == version.csv_data_for_download()


def test_get_with_fixed_headers(client, old_style_version):
    old_style_version.csv_data = old_style_version.csv_data.replace(
        "id,name", "code,name"
    )
    old_style_version.save()
    assert old_style_version.table[0] == ["code", "name"]
    rsp = client.get(old_style_version.get_download_url() + "?fixed-headers")
    data = rsp.content.decode("utf8")
    assert data == old_style_version.csv_data_for_download(fixed_headers=True)
    assert csv_data_to_rows(data)[0] == ["code", "term"]


def test_get_with_fixed_headers_no_matching_term(client, old_style_version):
    old_style_version.csv_data = old_style_version.csv_data.replace(
        "code,name", "id,unk_description"
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
        "code,name", "unk,name"
    )
    old_style_version.save()
    assert not old_style_version.downloadable
    rsp = client.get(old_style_version.get_download_url() + "?fixed-headers")
    assert rsp.status_code == 400


def test_get_with_mapped_vmps(client, dmd_version_asthma_medication):
    # create a previous mapping for one of the dmd codes
    Mapping.objects.create(id="10514511000001106", vpidprev="999")
    # create a new mapping for one of the dmd codes
    Mapping.objects.create(id="888", vpidprev="10514511000001106")

    rsp = client.get(dmd_version_asthma_medication.get_download_url())
    data = rsp.content.decode("utf8")
    # Includes mapped VMPs by default, and uses fixed headers
    assert csv_data_to_rows(data) == [
        ["code", "term"],
        ["10514511000001106", "Adrenaline (base) 220micrograms/dose inhaler"],
        ["10525011000001107", "Adrenaline (base) 220micrograms/dose inhaler refill"],
        ["999", "VMP previous to 10514511000001106"],
        ["888", "VMP subsequent to 10514511000001106"],
    ]


def test_get_with_duplicated_mapped_vmps(client, dmd_version_asthma_medication):
    # The dmd version has 2 codes, 10514511000001106 and 10525011000001107
    # So far in the data, we only have mappings from a single VMP code to another
    # VMP code (barring a few mapping from a code to itself, which we ignore)
    # However, it could be possible that a VMP code could be split in a new
    # release (i.e. there are 2+ new codes mapping to the same old code)

    # create mappings for both of the codes to the same previous code
    Mapping.objects.create(id="10514511000001106", vpidprev="999")
    Mapping.objects.create(id="10525011000001107", vpidprev="999")

    # create new mappings from 2 different codes to the code 10514511000001106
    Mapping.objects.create(id="888", vpidprev="10514511000001106")
    Mapping.objects.create(id="777", vpidprev="10514511000001106")

    rsp = client.get(dmd_version_asthma_medication.get_download_url())
    data = rsp.content.decode("utf8")
    # Includes mapped VMPs by default, and uses fixed headers
    assert csv_data_to_rows(data) == [
        ["code", "term"],
        ["10514511000001106", "Adrenaline (base) 220micrograms/dose inhaler"],
        ["10525011000001107", "Adrenaline (base) 220micrograms/dose inhaler refill"],
        ["999", "VMP previous to 10514511000001106, 10525011000001107"],
        ["888", "VMP subsequent to 10514511000001106"],
        ["777", "VMP subsequent to 10514511000001106"],
    ]


def test_get_without_mapped_vmps(client, dmd_version_asthma_medication):
    # create a mapping for one of the dmd codes
    Mapping.objects.create(id="10514511000001106", vpidprev="999")
    rsp = client.get(
        dmd_version_asthma_medication.get_download_url() + "?omit-mapped-vmps"
    )
    data = rsp.content.decode("utf8")
    # omitting mapped VMPs, just download the CSV data as is
    rows = csv_data_to_rows(data)
    assert rows[0] == ["dmd_type", "dmd_id", "dmd_name", "bnf_code"]
    # Mapped VMPS are not in the download
    assert [row[1] for row in rows] == [
        "dmd_id",
        "10514511000001106",
        "10525011000001107",
    ]
