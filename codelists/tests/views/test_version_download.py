import pytest

from mappings.dmdvmpprevmap.models import Mapping
from opencodelists.csv_utils import csv_data_to_rows


def test_get(client, version):
    rsp = client.get(version.get_download_url())
    data = rsp.content.decode("utf8")
    assert data == version.csv_data_for_download()


def test_get_with_original_headers(client, old_style_version):
    # by default, the original csv data is downloaded
    rsp = client.get(old_style_version.get_download_url())
    data = rsp.content.decode("utf8")
    assert data == old_style_version.csv_data_for_download()
    assert csv_data_to_rows(data)[0] == ["code", "name"]


def test_get_with_fixed_headers(client, old_style_version):
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
    # Includes mapped VMPs  and uses fixed headers by default
    # Includes an additional column with the original code header
    assert csv_data_to_rows(data) == [
        ["code", "term", "dmd_id", "dmd_type", "bnf_code"],
        [
            "10514511000001106",
            "Adrenaline (base) 220micrograms/dose inhaler",
            "10514511000001106",
            "VMP",
            "0301012A0AAABAB",
        ],
        [
            "10525011000001107",
            "Adrenaline (base) 220micrograms/dose inhaler refill",
            "10525011000001107",
            "VMP",
            "0301012A0AAACAC",
        ],
        [
            "999",
            "VMP previous to 10514511000001106",
            "999",
            "VMP",
            "0301012A0AAABAB",
        ],
        [
            "888",
            "VMP subsequent to 10514511000001106",
            "888",
            "VMP",
            "0301012A0AAABAB",
        ],
    ]


def test_get_with_mapped_vmps_and_original_code_column(
    client, dmd_version_asthma_medication
):
    dmd_version_asthma_medication.csv_data = (
        dmd_version_asthma_medication.csv_data.replace("dmd_id", "code")
    )
    dmd_version_asthma_medication.save()

    # create a previous mapping for one of the dmd codes
    Mapping.objects.create(id="10514511000001106", vpidprev="999")

    rsp = client.get(dmd_version_asthma_medication.get_download_url())
    data = rsp.content.decode("utf8")
    # Includes mapped VMPs by default, and uses fixed headers
    # No additional column when the original code column was already "code"
    assert csv_data_to_rows(data) == [
        ["code", "term", "dmd_type", "bnf_code"],
        [
            "10514511000001106",
            "Adrenaline (base) 220micrograms/dose inhaler",
            "VMP",
            "0301012A0AAABAB",
        ],
        [
            "10525011000001107",
            "Adrenaline (base) 220micrograms/dose inhaler refill",
            "VMP",
            "0301012A0AAACAC",
        ],
        [
            "999",
            "VMP previous to 10514511000001106",
            "VMP",
            "0301012A0AAABAB",
        ],
    ]


@pytest.mark.parametrize(
    "csv_data,expected",
    [
        (
            "dmd_id\n10514511000001106\n10525011000001107",
            [
                ["code", "term", "dmd_id"],
                ["10514511000001106", "", "10514511000001106"],
                ["10525011000001107", "", "10525011000001107"],
                ["999", "VMP previous to 10514511000001106", "999"],
                ["888", "VMP subsequent to 10514511000001106", "888"],
            ],
        ),
        (
            "code\n10514511000001106\n10525011000001107",
            [
                ["code", "term"],
                ["10514511000001106", ""],
                ["10525011000001107", ""],
                ["999", "VMP previous to 10514511000001106"],
                ["888", "VMP subsequent to 10514511000001106"],
            ],
        ),
        (
            "dmd_id,dmd_type,bnf_code\n"
            "10514511000001106,VMP,0301012A0AAABAB\n10525011000001107,VMP,0301012A0AAACAC",
            [
                ["code", "term", "dmd_id", "dmd_type", "bnf_code"],
                [
                    "10514511000001106",
                    "",
                    "10514511000001106",
                    "VMP",
                    "0301012A0AAABAB",
                ],
                [
                    "10525011000001107",
                    "",
                    "10525011000001107",
                    "VMP",
                    "0301012A0AAACAC",
                ],
                [
                    "999",
                    "VMP previous to 10514511000001106",
                    "999",
                    "VMP",
                    "0301012A0AAABAB",
                ],
                [
                    "888",
                    "VMP subsequent to 10514511000001106",
                    "888",
                    "VMP",
                    "0301012A0AAABAB",
                ],
            ],
        ),
    ],
)
def test_get_with_mapped_vmps_no_term_column(
    client, dmd_version_asthma_medication, csv_data, expected
):
    # create a previous mapping for one of the dmd codes
    Mapping.objects.create(id="10514511000001106", vpidprev="999")
    # create a new mapping for one of the dmd codes
    Mapping.objects.create(id="888", vpidprev="10514511000001106")

    # update CSV data
    dmd_version_asthma_medication.csv_data = csv_data
    dmd_version_asthma_medication.save()

    rsp = client.get(dmd_version_asthma_medication.get_download_url())
    data = rsp.content.decode("utf8")
    # Includes mapped VMPs  and uses fixed headers by default
    # Includes an additional column with the original code header
    assert csv_data_to_rows(data) == expected


def test_get_with_mapped_vmps_and_fixed_headers(client, dmd_version_asthma_medication):
    # create a previous mapping for one of the dmd codes
    Mapping.objects.create(id="10514511000001106", vpidprev="999")
    # create a new mapping for one of the dmd codes
    Mapping.objects.create(id="888", vpidprev="10514511000001106")

    rsp = client.get(
        dmd_version_asthma_medication.get_download_url() + "?fixed-headers"
    )
    data = rsp.content.decode("utf8")
    # Includes mapped VMPs by default, and uses fixed headers
    # No additional column with the original code header when fixed headers are explictly requested
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
        ["code", "term", "dmd_id", "dmd_type", "bnf_code"],
        [
            "10514511000001106",
            "Adrenaline (base) 220micrograms/dose inhaler",
            "10514511000001106",
            "VMP",
            "0301012A0AAABAB",
        ],
        [
            "10525011000001107",
            "Adrenaline (base) 220micrograms/dose inhaler refill",
            "10525011000001107",
            "VMP",
            "0301012A0AAACAC",
        ],
        [
            "999",
            "VMP previous to 10514511000001106, 10525011000001107",
            "999",
            "VMP",
            "0301012A0AAABAB",
        ],
        ["777", "VMP subsequent to 10514511000001106", "777", "VMP", "0301012A0AAABAB"],
        ["888", "VMP subsequent to 10514511000001106", "888", "VMP", "0301012A0AAABAB"],
    ]


def test_get_with_mapped_vmps_nothing_to_map(client, dmd_version_asthma_medication):
    # Test that the download still works even if there are no relevant mapped VMPs
    # create a previous mapping for some other unrelated dmd code
    Mapping.objects.create(id="111", vpidprev="999")
    rsp = client.get(dmd_version_asthma_medication.get_download_url())
    data = rsp.content.decode("utf8")

    assert csv_data_to_rows(data) == [
        ["code", "term", "dmd_id", "dmd_type", "bnf_code"],
        [
            "10514511000001106",
            "Adrenaline (base) 220micrograms/dose inhaler",
            "10514511000001106",
            "VMP",
            "0301012A0AAABAB",
        ],
        [
            "10525011000001107",
            "Adrenaline (base) 220micrograms/dose inhaler refill",
            "10525011000001107",
            "VMP",
            "0301012A0AAACAC",
        ],
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


def test_get_with_mapped_vmps_more_than_one_step_distant(
    client, dmd_version_asthma_medication
):
    # create a previous mapping for one of the dmd codes
    Mapping.objects.create(id="10514511000001106", vpidprev="999")
    # create a previous mapping for this previous code
    # create two more mapping for one of the dmd codes; neither of these
    # codes are in the codelist, but 777 and 666 need to be mapped in as a previous
    # code to 10514511000001106, which is in the codelist
    Mapping.objects.create(id="999", vpidprev="777")
    Mapping.objects.create(id="777", vpidprev="666")

    # create some new mappings for one of the dmd codes
    Mapping.objects.create(id="AAA", vpidprev="10514511000001106")
    Mapping.objects.create(id="BBB", vpidprev="AAA")
    Mapping.objects.create(id="CCC", vpidprev="BBB")

    rsp = client.get(dmd_version_asthma_medication.get_download_url())
    data = rsp.content.decode("utf8")
    assert csv_data_to_rows(data) == [
        ["code", "term", "dmd_id", "dmd_type", "bnf_code"],
        [
            "10514511000001106",
            "Adrenaline (base) 220micrograms/dose inhaler",
            "10514511000001106",
            "VMP",
            "0301012A0AAABAB",
        ],
        [
            "10525011000001107",
            "Adrenaline (base) 220micrograms/dose inhaler refill",
            "10525011000001107",
            "VMP",
            "0301012A0AAACAC",
        ],
        ["666", "VMP previous to 10514511000001106", "666", "VMP", "0301012A0AAABAB"],
        ["777", "VMP previous to 10514511000001106", "777", "VMP", "0301012A0AAABAB"],
        ["999", "VMP previous to 10514511000001106", "999", "VMP", "0301012A0AAABAB"],
        ["AAA", "VMP subsequent to 10514511000001106", "AAA", "VMP", "0301012A0AAABAB"],
        ["BBB", "VMP subsequent to 10514511000001106", "BBB", "VMP", "0301012A0AAABAB"],
        ["CCC", "VMP subsequent to 10514511000001106", "CCC", "VMP", "0301012A0AAABAB"],
    ]
