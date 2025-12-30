import pytest

from mappings.bnfdmd.data_downloader import Downloader

from .conftest import MOCK_FILENAME


def test_download_latest_release(mocked_responses_homepage_zipfile, tmp_path):
    downloader = Downloader(tmp_path)
    release_zipfile_path, _ = downloader.download_latest_release()
    assert release_zipfile_path.exists()
    assert release_zipfile_path.name == MOCK_FILENAME


def test_get_latest_release_with_existing(mocked_responses_homepage, tmp_path):
    (tmp_path / MOCK_FILENAME).touch()
    downloader = Downloader(tmp_path)
    with pytest.raises(ValueError, match="Latest release already exists"):
        downloader.download_latest_release()


def test_historical_release_dates_parsed(mocked_responses_homepage, tmp_path):
    downloader = Downloader(tmp_path)
    releases = downloader.get_releases()

    assert len(releases) == 3
