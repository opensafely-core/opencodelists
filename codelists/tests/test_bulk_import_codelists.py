from os import environ
from pathlib import Path

import pytest

from ..models import Codelist, CodelistVersion
from ..scripts.bulk_import_codelists import main, process_file_to_dataframe


FIXTURES_PATH = Path(__file__).parent / "fixtures"

"""
The .txt fixture file and its associated config are the most comprehensive in terms of
covering bulk_import_codelists.main and thus are used for its test.

The older .xslx fixture file is not tested with main() due to weird database problems
with calling multiple tests marked with @pytest.mark.django_db in the same session.
Therefore, the processing of an excel file into a dataframe is tested in isolation
as it is the only aspect that is not tested by test_import_from_txt
"""


@pytest.mark.django_db(
    transaction=True,
    databases=["default", "snomedct_test_20200101"],
)
def test_import_from_txt(
    snomedct_data, organisation, organisation_user, live_server, capsys
):
    config = {
        "organisation": "test-university",
        "sheet": "codelists",
        "coding_systems": {
            "SNOMED CT": {"id": "snomedct", "release": "snomedct_test_20200101"},
        },
        "column_aliases": {
            "code": "Alias for Code",
            "codelist_description": "codelist_code",
        },
        "codelist_name_aliases": {
            "Name to alias to Tennis Toe": "Tennis Toe",
        },
        "delimiter": "\t",
        "tag": "1234",
        "description_template": "Taken from the %s reference list",
    }

    file_path = FIXTURES_PATH / "codelists.txt"

    url = live_server.url
    environ["API_TOKEN"] = organisation_user.api_token

    expected_cl_count = Codelist.objects.count()
    expected_clv_count = CodelistVersion.objects.count()

    # dry_run is the default, and doesn't actually create anything
    main(file_path, config, host=url)
    assert Codelist.objects.count() == expected_cl_count
    assert CodelistVersion.objects.count() == expected_clv_count

    # importing txt file creates 2 new codelists
    main(file_path, config, dry_run=False, host=url)
    expected_cl_count += 2
    expected_clv_count += 2
    assert Codelist.objects.count() == expected_cl_count
    assert CodelistVersion.objects.count() == expected_clv_count

    # test description string interpolation
    for code in ["ART2", "TEN2"]:
        description = config["description_template"] % code
        assert Codelist.objects.filter(description=description).count() == 1

    # test version tag set
    assert CodelistVersion.objects.filter(tag=config["tag"]).count() == 2

    # increment tag to avoid violating UNIQUE constraint
    config["tag"] = "5678"

    # reimporting again creates new versions for the existing codelists
    main(
        file_path,
        config,
        dry_run=False,
        host=url,
        force_new_version=True,
    )
    expected_clv_count += 2
    assert Codelist.objects.count() == expected_cl_count
    assert CodelistVersion.objects.count() == expected_clv_count

    # increment tag to avoid violating UNIQUE constraint
    config["tag"] = "9012"

    # Limit to named codelists and reimport again; creates a new version
    # for the named codelist only
    config["limit_to_named_codelists"] = True
    main(
        file_path,
        config,
        dry_run=False,
        host=url,
        force_new_version=True,
    )
    expected_clv_count += 1
    assert Codelist.objects.count() == expected_cl_count
    assert CodelistVersion.objects.count() == expected_clv_count

    # Test that if the first API call fails then the script exits early with
    # the correct message. We can't test this in a separate tests due to the
    # limitations described above
    # increment tag to avoid violating UNIQUE constraint
    config["tag"] = "9013"
    environ["API_TOKEN"] = "invalid-token"
    with pytest.raises(SystemExit):
        main(file_path, config, host=url, dry_run=False)

    captured = capsys.readouterr()
    assert (
        "The first API call failed, so no further attempts will be made" in captured.out
    )


def test_process_file_to_dataframe_excel():
    config = {
        "organisation": "test-university",
        "sheet": "codelists",
        "coding_systems": {
            "SNOMED CT": {"id": "snomedct", "release": "snomedct_test_20200101"},
            "dm+d": {"id": "dmd", "release": "dmd_test_20200101"},
        },
        "column_aliases": {
            "code": "Alias for Code",
        },
        "codelist_name_aliases": {
            "Name to alias to Asthma meds": "Asthma meds",
        },
    }
    file_path = FIXTURES_PATH / "codelists.xlsx"

    df = process_file_to_dataframe(file_path, config)

    assert len(df) == 5
    assert set(df.columns) == {"coding_system", "codelist_name", "code", "term"}
    for col in df.columns:
        assert not any(df[col].isna())
    assert set(df.coding_system.unique()) == {"SNOMED CT", "dm+d"}
    assert set(df.codelist_name.unique()) == {"Arthritis", "Asthma meds"}
