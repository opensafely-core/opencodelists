from pathlib import Path
from unittest.mock import patch
from urllib.parse import quote

import pytest
import responses


MOCK_BNFDMD_IMPORT_DATA_PATH = (
    Path(__file__).parents[1]
    / "fixtures"
    / "import_resources"
    / "BNF Snomed Mapping data 20241119.zip"
)

MOCK_FILENAME = "BNF Snomed Mapping data 20240101.zip"
MOCK_QUOTED_FILENAME = quote(MOCK_FILENAME)
MOCK_FILEPATH = f"2024-01/{MOCK_QUOTED_FILENAME}"


@pytest.fixture
def mocked_responses_homepage_zipfile(mocked_responses_homepage):
    with MOCK_BNFDMD_IMPORT_DATA_PATH.open("rb") as f:
        mocked_responses_homepage.add(
            responses.GET,
            f"https://www.nhsbsa.nhs.uk/sites/default/files/{MOCK_FILEPATH}",
            content_type="application/zip",
            body=f,
            status=200,
        )
        yield mocked_responses_homepage


@pytest.fixture
def mocked_responses_homepage():
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            "https://www.nhsbsa.nhs.uk/prescription-data/understanding-our-data/bnf-snomed-mapping",
            body=f"""
            <p><a href="/sites/default/files/{MOCK_FILEPATH}">January 2024 (ZIP file: 16.76MB)</a></p>
            <p><a href="/sites/default/files/2023-01/BNF%20Snomed%20Mapping%20data%2020230116.zip">January</a> 2023 (ZIP file: 16.76MB)</p>
            <p>September<a href="/sites/default/files/2023-11/BNF%20Snomed%20Mapping%20data%2020231120.zip"> 2023 (ZIP file: 18.77MB)</a></p>
        """,
            status=200,
        )
        yield rsps


@pytest.fixture
def mock_data_download(mocked_responses_homepage):
    with patch(
        "mappings.bnfdmd.data_downloader.Downloader.get_file",
        return_value=MOCK_QUOTED_FILENAME,
    ):
        yield
