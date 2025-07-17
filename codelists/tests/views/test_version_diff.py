import pytest

from codelists.views.version_diff import summarise


def test_get(client, version_with_no_searches, version_with_some_searches):
    rsp = client.get(version_with_no_searches.get_diff_url(version_with_some_searches))
    assert rsp.status_code == 200

    rsp = client.get(version_with_some_searches.get_diff_url(version_with_no_searches))
    assert rsp.status_code == 200


def test_summarise(version_with_no_searches, version_with_some_searches):
    lhs_codes = set(version_with_no_searches.codes)
    rhs_codes = set(version_with_some_searches.codes)
    rhs_only_codes = rhs_codes - lhs_codes
    assert summarise(rhs_only_codes, version_with_no_searches.coding_system) == [
        {
            "code": "439656005",
            "descendants": [{"code": "202855006", "term": "Lateral epicondylitis"}],
            "term": "Arthritis of elbow",
        }
    ]


def test_get_dmd_diff_codes_match(
    client, dmd_version_asthma_medication, dmd_version_asthma_medication_alt_headers
):
    # codelists have identical codes, different CSV headers
    # 2 codes only:
    # 10514511000001106 - Adrenaline (base) 220micrograms/dose inhaler
    # 10525011000001107 - Adrenaline (base) 220micrograms/dose inhaler refill

    rsp = client.get(
        dmd_version_asthma_medication.get_diff_url(
            dmd_version_asthma_medication_alt_headers
        )
    )
    assert rsp.context["common_codes"] == {"10514511000001106", "10525011000001107"}
    assert rsp.context["rhs_only_codes"] == rsp.context["lhs_only_codes"] == set()


def test_get_dmd_diff_codes_differ(
    client, dmd_version_asthma_medication, dmd_version_asthma_medication_refill
):
    # codelists have one common code, one different
    # terms for the common code differ but are extracted from the coding system, so are
    # summarised identically
    # Code 123 is unknown in the coding system; it is displayed with the data from the CSV
    # dmd_version_asthma_medication
    # 10514511000001106 - Adrenaline (base) 220micrograms/dose inhaler
    # 10525011000001107 - Adrenaline (base) 220micrograms/dose inhaler refill
    # dmd_version_asthma_medication_refill
    # 10525011000001107 - Adrenaline (base) 220micrograms/dose inhaler refill X
    # 123 - Test refill
    rsp = client.get(
        dmd_version_asthma_medication.get_diff_url(dmd_version_asthma_medication_refill)
    )
    assert rsp.context["common_codes"] == {"10525011000001107"}
    assert rsp.context["lhs_only_codes"] == {"10514511000001106"}
    assert rsp.context["rhs_only_codes"] == {"123"}
    assert rsp.context["rhs_only_summary"] == [
        {"code": "123", "term": "[Unknown] Test refill (VMP)", "descendants": []}
    ]
    assert rsp.context["common_summary"] == [
        {
            "code": "10525011000001107",
            "term": "Adrenaline (base) 220micrograms/dose inhaler refill (VMP)",
            "descendants": [],
        }
    ]


@pytest.mark.parametrize(
    "rhs_column_names,expected_unknown_term",
    [
        ("type,dmd,nm,bnf_code", "[Unknown] Test refill (VMP)"),
        ("type,id,name,bnf_code", "[Unknown] Test refill (VMP)"),
        ("obj_type,code,dmd_name,bnf_code", "[Unknown] Test refill (VMP)"),
        ("dmd_type,snomed_id,term,bnf_code", "[Unknown] Test refill (VMP)"),
        # no type column name found
        ("unk,snomed_id,term,bnf_code", "[Unknown] Test refill"),
        # no term column name found
        ("type,snomed_id,unk,bnf_code", "Unknown"),
        # neither term or type column name found
        ("unk1,snomed_id,unk2,bnf_code", "Unknown"),
    ],
)
def test_get_dmd_diff_alternative_column_names(
    client,
    dmd_version_asthma_medication,
    dmd_version_asthma_medication_refill,
    rhs_column_names,
    expected_unknown_term,
):
    # codelists have one common code, one different
    # terms for the common code differ but are extracted from the coding system, so are
    # summarised identically
    # Code 123 is unknown in the coding system; it is displayed with the data from the CSV
    # dmd_version_asthma_medication
    # 10514511000001106 - Adrenaline (base) 220micrograms/dose inhaler
    # 10525011000001107 - Adrenaline (base) 220micrograms/dose inhaler refill
    # dmd_version_asthma_medication_refill
    # 10525011000001107 - Adrenaline (base) 220micrograms/dose inhaler refill X
    # 123 - Test refill

    # in the fixtures, the column names are: dmd_type, dmd_id, dmd_name, bnf_code
    # test that different column names can be used to fetch the same data
    replacement_csv_data = dmd_version_asthma_medication_refill.csv_data.replace(
        "dmd_type,dmd_id,dmd_name,bnf_code", rhs_column_names
    )
    dmd_version_asthma_medication_refill.csv_data = replacement_csv_data
    dmd_version_asthma_medication_refill.save()
    assert dmd_version_asthma_medication_refill.table[0] == rhs_column_names.split(",")
    rsp = client.get(
        dmd_version_asthma_medication.get_diff_url(dmd_version_asthma_medication_refill)
    )
    assert rsp.context["common_codes"] == {"10525011000001107"}
    assert rsp.context["lhs_only_codes"] == {"10514511000001106"}
    assert rsp.context["rhs_only_codes"] == {"123"}
    assert rsp.context["rhs_only_summary"] == [
        {"code": "123", "term": expected_unknown_term, "descendants": []}
    ]
    assert rsp.context["common_summary"] == [
        {
            "code": "10525011000001107",
            "term": "Adrenaline (base) 220micrograms/dose inhaler refill (VMP)",
            "descendants": [],
        }
    ]


def test_get_dmd_diff_no_code_column(
    client,
    dmd_version_asthma_medication,
    dmd_version_asthma_medication_refill,
):
    # in the fixtures, the column names are: dmd_type, dmd_id, dmd_name, bnf_code
    # rename the code column in one codelist version so no matching code column
    # will be foung
    replacement_csv_data = dmd_version_asthma_medication_refill.csv_data.replace(
        "dmd_type,dmd_id,dmd_name,bnf_code",
        "dmd_type,unk_id,dmd_name,bnf_code",
    )
    dmd_version_asthma_medication_refill.csv_data = replacement_csv_data
    dmd_version_asthma_medication_refill.save()
    rsp = client.get(
        dmd_version_asthma_medication.get_diff_url(dmd_version_asthma_medication_refill)
    )
    assert rsp.status_code == 400
    assert rsp.text == "Could not identify code columns"


def test_get_snomed_diff_new_vs_old_style_with_unknown(
    client, version_with_no_searches, old_style_version
):
    # old_style_version has CSV data; add an unknown code so we can test the term can be
    # retrieved from the CSV data
    old_style_version.csv_data += "1234,Test code\n"
    old_style_version.save()
    rsp = client.get(version_with_no_searches.get_diff_url(old_style_version))
    assert rsp.context["rhs_only_codes"] == {"1234", "202855006", "439656005"}
    assert rsp.context["common_codes"] == {
        "35185008",
        "156659008",
        "239964003",
        "73583000",
        "128133004",
        "429554009",
    }
    assert rsp.context["lhs_only_codes"] == set()
    assert rsp.context["rhs_only_summary"] == [
        {
            "code": "439656005",
            "term": "Arthritis of elbow",
            "descendants": [{"code": "202855006", "term": "Lateral epicondylitis"}],
        },
        {"code": "1234", "term": "[Unknown] Test code", "descendants": []},
    ]


def test_get_version_diff_no_matching_version(
    client, version_with_no_searches, old_style_version
):
    url = version_with_no_searches.get_diff_url(old_style_version)
    url = url.replace(old_style_version.hash, "unknown-version-hash")
    rsp = client.get(url)
    assert rsp.status_code == 404


def test_version_diff_default_columns(client, null_codelist):
    # null_codelist has 2 old-style versions
    # null coding_system doesn't have any named code/term columns, so
    # should use the defaults
    version1, version2 = list(null_codelist.versions.all())
    rsp = client.get(version1.get_diff_url(version2))
    assert rsp.context["rhs_only_codes"] == {"5678"}
    assert rsp.context["lhs_only_codes"] == {"1234"}
