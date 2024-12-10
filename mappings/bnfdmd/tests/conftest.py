from unittest.mock import patch

import pytest
import responses


def add_response(rsps, filename, release_date):
    rsps.add(
        responses.GET,
        "https://www.nhsbsa.nhs.uk/prescription-data/understanding-our-data/bnf-snomed-mapping",
        body=f"""
            <p><a href="/sites/default/files/{release_date}/{filename.replace(' ','%20')}">January 2024 (ZIP file: 16.76MB)</a></p>
            <p><a href="/sites/default/files/2023-01/BNF%20Snomed%20Mapping%20data%2020230116.zip">January 2023 (ZIP file: 16.76MB)</a></p>
        """,
        status=200,
    )


@pytest.fixture
def mocked_responses():
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def mock_data_download(mocked_responses):
    filename = "BNF%20Snomed%20Mapping%20data%2020240101.zip"
    add_response(mocked_responses, filename, "2024-01")
    with patch(
        "mappings.bnfdmd.data_downloader.Downloader.get_file",
        return_value=filename,
    ):
        yield
