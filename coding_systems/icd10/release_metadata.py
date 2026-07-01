"""
Build and compare metadata for the WHO ICD-10 ClaML ZIP files.
"""

import json
import zipfile
from datetime import date
from pathlib import Path

import structlog

from coding_systems.icd10.data_downloader import (
    SOURCE_URL,
    download_zip,
    get_release_metadata,
)


YEARS = ["2016", "2019"]
DEFAULT_RELEASE_DIR = Path(__file__).parent / "data"
DEFAULT_RECORD_PATH = DEFAULT_RELEASE_DIR / "claml_metadata.json"


logger = structlog.get_logger()


def xml_file_info(zip_path: Path) -> zipfile.ZipInfo:
    """Return the single XML member from a downloaded ICD-10 ClaML ZIP file."""
    with zipfile.ZipFile(zip_path) as zf:
        xml_members = [
            info
            for info in zf.infolist()
            if not info.is_dir() and Path(info.filename).suffix.lower() == ".xml"
        ]

    if len(xml_members) != 1:
        filenames = [info.filename for info in xml_members]
        raise ValueError(
            f"Expected exactly one XML file in {zip_path}, found {filenames}"
        )

    return xml_members[0]


def release_record(release_dir: Path, year: str) -> dict:
    """Download a release ZIP and return metadata for its XML member."""
    metadata = get_release_metadata(year)
    zip_path = download_zip(release_dir, year, force_download=True)
    info = xml_file_info(zip_path)

    return {
        "url": metadata["url"],
        "zip_filename": metadata["zip_filename"],
        "xml_filename": info.filename,
        "xml_last_updated": date(*info.date_time[:3]).isoformat(),
        "xml_file_size": info.file_size,
    }


def build_record(release_dir: Path) -> dict:
    """Build the current metadata record for all tracked WHO ClaML releases."""
    return {
        "source": SOURCE_URL,
        "releases": {year: release_record(release_dir, year) for year in YEARS},
    }


def check_claml_zip_metadata(
    release_dir: Path = DEFAULT_RELEASE_DIR, record_path: Path = DEFAULT_RECORD_PATH
) -> None:
    """
    Refresh WHO ZIP metadata and write it if it differs from the saved record.

    The generated JSON is stable, so any upstream timestamp or file-size change
    is visible in git diff.
    """
    record_path.parent.mkdir(parents=True, exist_ok=True)

    record = build_record(release_dir)

    if record_path.exists():
        existing_record = json.loads(record_path.read_text())

        if existing_record == record:
            logger.info("No changes detected in ClaML file metadata.")
            return
        else:
            logger.warning(
                "\n⚠️  CHANGE DETECTED  ⚠️\n\n"
                "Something has changed in the online xml files when "
                "compared to the existing record. See the diff in:\n\n"
                f"  {record_path}\n"
            )

    record_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
