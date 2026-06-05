"""
Refresh the WHO ICD-10 ClaML ZIPs and record the timestamp of their XML member.

The output is stable JSON so a subsequent run makes any upstream change visible
in git diff.

Usage:

    python -m coding_systems.icd10.scripts.check_icd10_claml_zip_timestamps
"""

import json
import zipfile
from datetime import date
from pathlib import Path

from coding_systems.icd10.data_downloader import (
    download_zip,
    get_release_metadata,
)


ICD10_ROOT = Path(__file__).parent.parent
RELEASE_DIR = ICD10_ROOT / "data"
RECORD_PATH = RELEASE_DIR / "claml_metadata.json"
YEARS = ["2016", "2019"]


def xml_file_info(zip_path: Path) -> zipfile.ZipInfo:
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
    return {
        "source": "https://icdcdn.who.int/icd10/index.html",
        "releases": {year: release_record(release_dir, year) for year in YEARS},
    }


def main() -> None:
    RECORD_PATH.parent.mkdir(parents=True, exist_ok=True)

    record = build_record(RELEASE_DIR)

    if RECORD_PATH.exists():
        existing_record = json.loads(RECORD_PATH.read_text())

        if existing_record == record:
            print(
                "\n✅ There are no changes to the timestamp, or size, of the "
                "ClaML files when compared to the existing record.\n"
            )
            return
        else:
            print(
                "\n⚠️  CHANGE DETECTED  ⚠️\n\n"
                "Something has changed in the online xml files when "
                "compared to the existing record. See the diff in:\n\n"
                f"  {RECORD_PATH}\n"
            )

    RECORD_PATH.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
