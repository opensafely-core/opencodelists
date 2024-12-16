from os import environ
from pathlib import Path

import pytest

from ..models import Codelist, CodelistVersion
from ..scripts.bulk_import_codelists import main


FIXTURES_PATH = Path(__file__).parent / "fixtures"


@pytest.mark.django_db(
    transaction=True,
    databases=["default", "snomedct_test_20200101", "dmd_test_20200101"],
)
def test_import_from_xlsx(
    snomedct_data, dmd_data, organisation, organisation_user, live_server
):
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

    url = live_server.url
    environ["API_TOKEN"] = organisation_user.api_token

    expected_cl_count = Codelist.objects.count()
    expected_clv_count = CodelistVersion.objects.count()

    # dry_run is the default, and doesn't actually create anything
    main(FIXTURES_PATH / "codelists.xlsx", config, host=url)
    assert Codelist.objects.count() == expected_cl_count
    assert CodelistVersion.objects.count() == expected_clv_count

    # importing xlsx file creates 2 new codelists
    main(FIXTURES_PATH / "codelists.xlsx", config, dry_run=False, host=url)
    expected_cl_count += 2
    expected_clv_count += 2
    assert Codelist.objects.count() == expected_cl_count
    assert CodelistVersion.objects.count() == expected_clv_count

    # reimporting again creates new versions for the existing codelists
    main(
        FIXTURES_PATH / "codelists.xlsx",
        config,
        dry_run=False,
        host=url,
        force_new_version=True,
    )
    expected_clv_count += 2
    assert Codelist.objects.count() == expected_cl_count
    assert CodelistVersion.objects.count() == expected_clv_count

    # Limit to named codelists and reimport again; creates a new version
    # for the named codelist only
    config["limit_to_named_codelists"] = True
    main(
        FIXTURES_PATH / "codelists.xlsx",
        config,
        dry_run=False,
        host=url,
        force_new_version=True,
    )
    expected_clv_count += 1
    assert Codelist.objects.count() == expected_cl_count
    assert CodelistVersion.objects.count() == expected_clv_count
