from pathlib import Path
from unittest.mock import patch

import pytest
import responses
from django.conf import settings

from coding_systems.conftest import mock_migrate_coding_system

MOCK_SNOMEDCT_IMPORT_DATA_PATH = (
    Path(__file__).parents[1] / "fixtures" / "import_resources"
)


@pytest.fixture(autouse=True)
def mock_migrate():
    with patch(
        "coding_systems.base.import_data_utils.call_command", mock_migrate_coding_system
    ):
        yield


def add_response(rsps, filename, release_date):
    rsps.add(
        responses.GET,
        f"https://isd.digital.nhs.uk/trud/api/v1/keys/{settings.TRUD_API_KEY}/items/101/releases",
        json={
            "api": "v1",
            "releases": [
                {
                    "id": "latest",
                    "archiveFileName": filename,
                    "archiveFileUrl": f"https://download/{filename}",
                    "releaseDate": release_date,
                },
                {
                    "id": "1",
                    "archiveFileName": "uk_sct2cl_1.0.0_20220101000001Z.zip",
                    "archiveFileUrl": "https://download/uk_sct2cl_1.0.0_20220101000001Z.zip",
                    "releaseDate": "2022-01-01",
                },
            ],
        },
        status=200,
    )


@pytest.fixture
def mocked_responses():
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def mock_data_download(mocked_responses):
    filename = "uk_sct2cl_2.0.0_20230101000001Z.zip"
    add_response(mocked_responses, filename, "2023-01-01")
    with patch(
        "coding_systems.snomedct.import_data.SnomedctTrudDownloader.get_file",
        return_value=filename,
    ):
        yield
