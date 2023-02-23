import shutil
from pathlib import Path
from unittest.mock import patch

import pytest
import responses
from django.conf import settings

from coding_systems.conftest import mock_migrate_coding_system

MOCK_DMD_IMPORT_DATA_PATH = Path(__file__).parents[1] / "fixtures" / "import_resources"


@pytest.fixture(autouse=True)
def mock_migrate():
    with patch(
        "coding_systems.base.import_data_utils.call_command", mock_migrate_coding_system
    ):
        yield


def add_response(rsps, filename, release_date):
    rsps.add(
        responses.GET,
        f"https://isd.digital.nhs.uk/trud/api/v1/keys/{settings.TRUD_API_KEY}/items/24/releases",
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
                    "archiveFileName": "nhsbsa_dmd_2.0.0_20220101000001.zip",
                    "archiveFileUrl": "https://download/nhsbsa_dmd_2.0.0_20220101000001.zip",
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
    filename = "nhsbsa_dmd_1.0.0_20221001000001.zip"
    add_response(mocked_responses, filename, "2022-10-01")
    with patch(
        "coding_systems.dmd.import_data.DMDTrudDownloader.get_file",
        return_value=filename,
    ):
        yield


@pytest.fixture
def mock_data_download_error(mocked_responses):
    # make a temporary copy of the good data with new filename
    original_filename = "nhsbsa_dmd_1.0.0_20221001000001.zip"
    new_filename = "nhsbsa_dmd_1.0.1_20220901000001.zip"
    shutil.copy(
        MOCK_DMD_IMPORT_DATA_PATH / original_filename,
        MOCK_DMD_IMPORT_DATA_PATH / new_filename,
    )
    add_response(mocked_responses, new_filename, "2022-09-01")
    with patch(
        "coding_systems.dmd.import_data.DMDTrudDownloader.get_file",
        return_value=new_filename,
    ):
        yield
    (MOCK_DMD_IMPORT_DATA_PATH / new_filename).unlink()


@pytest.fixture
def mock_data_download_bad_zip(mocked_responses):
    filename = "nhsbsa_dmd_1.1.0_20221001000001.zip"
    add_response(mocked_responses, filename, "2022-10-01")
    with patch(
        "coding_systems.dmd.import_data.DMDTrudDownloader.get_file",
        return_value=filename,
    ):
        yield


@pytest.fixture
def mock_data_download_no_prev_vmp(mocked_responses):
    filename = "nhsbsa_dmd_1.2.0_20221001000001.zip"
    add_response(mocked_responses, filename, "2022-10-01")
    with patch(
        "coding_systems.dmd.import_data.DMDTrudDownloader.get_file",
        return_value=filename,
    ):
        yield
