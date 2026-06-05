"""
Download and extract the WHO ICD-10 ClaML ZIP with local caching.
"""

import urllib.request
import zipfile
from pathlib import Path


def get_release_metadata(year: str) -> dict[str, str]:
    if year == "2019":
        return {
            "url": "https://icdcdn.who.int/icd10/claml/icd102019en.xml.zip",
            "zip_filename": "icd102019en.xml.zip",
            "xml_filename": "icd102019en.xml",
        }
    elif year == "2016":
        return {
            "url": "https://icdcdn.who.int/icd10/claml/icd102016en.xml.zip",
            "zip_filename": "icd102016en.xml.zip",
            "xml_filename": "icd102016en.xml",
        }
    else:
        raise ValueError(f"Unsupported year: {year}")


def download_zip(
    release_dir: Path, year: str = "2016", force_download: bool = False
) -> Path:
    """
    Ensure the ICD-10 ClaML ZIP file is available locally.
    """
    release_dir = Path(release_dir)
    release_dir.mkdir(parents=True, exist_ok=True)

    metadata = get_release_metadata(year)
    url = metadata["url"]
    zip_filename = metadata["zip_filename"]

    zip_path = release_dir / zip_filename

    if force_download or not zip_path.exists():
        urllib.request.urlretrieve(url, zip_path)

    return zip_path


def extract_xml_from_zip(
    zip_path: Path, year: str = "2016", force_download: bool = False
) -> Path:
    metadata = get_release_metadata(year)
    xml_filename = metadata["xml_filename"]
    xml_path = zip_path.parent / xml_filename

    if force_download or not xml_path.exists():
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extract(xml_filename, xml_path.parent)

    return xml_path


def download_release(
    release_dir,
    year: str = "2016",
    force_download: bool = False,
) -> Path:
    """
    Ensure the ICD-10 ClaML XML file is available locally.

    Downloads the ZIP if not already cached, then extracts it.
    Returns the path to the extracted XML file.
    """
    zip_path = download_zip(release_dir, year, force_download)
    xml_path = extract_xml_from_zip(zip_path, year, force_download)
    return xml_path
