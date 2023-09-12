from os import environ
from pathlib import Path

import pytest

from ..models import Codelist, CodelistVersion
from ..scripts.import_codelists_from_xlsx import main


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

    initial_cl_count = Codelist.objects.count()
    initial_clv_count = CodelistVersion.objects.count()

    # dry_run is the default, and doesn't actually create anything
    main(FIXTURES_PATH / "codelists.xlsx", config, host=url)
    assert Codelist.objects.count() == initial_cl_count
    assert CodelistVersion.objects.count() == initial_clv_count

    # importing xlsx file creates 2 new codelists
    main(FIXTURES_PATH / "codelists.xlsx", config, dry_run=False, host=url)
    assert Codelist.objects.count() == initial_cl_count + 2
    assert CodelistVersion.objects.count() == initial_clv_count + 2

    # reimporting again creates new versions for the existing codelists
    main(
        FIXTURES_PATH / "codelists.xlsx",
        config,
        dry_run=False,
        host=url,
        force_new_version=True,
    )
    assert Codelist.objects.count() == initial_cl_count + 2
    assert CodelistVersion.objects.count() == initial_clv_count + 4
