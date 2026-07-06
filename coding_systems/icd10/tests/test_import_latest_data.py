from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command


@patch("coding_systems.icd10.import_data.import_release", autospec=True)
def test_calls_import_release_function_with_release_metadata(
    mock_import_release, tmpdir, monkeypatch
):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    metadata = {
        "release_name": f"icd10_combined_{timestamp}",
        "filename": f"icd10_combined_{timestamp}.zip",
        "valid_from": timestamp,
        "file_metadata": {
            "WHO_2016": {
                "url": "https://icdcdn.who.int/icd10/claml/icd102016en.xml.zip",
                "zip_filename": "icd102016en.xml.zip",
                "xml_filename": "icd102016en.xml",
            },
            "WHO_2019": {
                "url": "https://icdcdn.who.int/icd10/claml/icd102019en.xml.zip",
                "zip_filename": "icd102019en.xml.zip",
                "xml_filename": "icd102019en.xml",
            },
            "NHS": {
                "url": "scraped",
                "zip_filename": f"icd10_nhs_scraped_{timestamp}.zip",
                "xml_filename": f"icd10_nhs_scraped_{timestamp}.xml",
            },
        },
    }

    def download_latest_release(self, force_download=False):
        return (
            Path(tmpdir) / f"icd10_combined_{timestamp}.zip",
            metadata,
        )

    monkeypatch.setattr(
        "coding_systems.icd10.data_downloader.Downloader.download_latest_release",
        download_latest_release,
    )

    call_command(
        "import_latest_data",
        "icd10",
        tmpdir,
    )
    mock_import_release.assert_called_once()
    mock_import_release.assert_called_with(
        Path(tmpdir) / f"icd10_combined_{timestamp}.zip",
        **metadata,
    )
