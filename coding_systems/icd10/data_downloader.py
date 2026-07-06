"""
Download and extract the WHO and scrape the NHS ICD-10 ClaML ZIP with local caching.
"""

import urllib.request
import zipfile
from datetime import datetime
from enum import Enum
from pathlib import Path

from coding_systems.icd10.scrape import scrape
from coding_systems.icd10.scraped_to_claml import convert_chapters_to_claml


class Year(Enum):
    WHO_2016 = "2016"
    WHO_2019 = "2019"
    NHS_2016 = "NHS"


class Downloader:
    def __init__(self, release_dir):
        self.who_url = "https://icdcdn.who.int/icd10/"
        self.release_dir = release_dir
        timestamp = datetime.now()
        self.valid_from = timestamp.date()
        self.timestamp = timestamp.strftime("%Y%m%d%H%M%S")

    def source_url(self):
        # The source for the claml files is currently this webpage. NB
        # the "index.html" is required to avoid 404 errors
        return self.who_url + "index.html"

    def get_release_metadata(self, year: Year) -> dict[str, str]:
        if year in [Year.WHO_2016, Year.WHO_2019]:
            return {
                "url": self.who_url + f"claml/icd10{year.value}en.xml.zip",
                "zip_filename": f"icd10{year.value}en.xml.zip",
                "xml_filename": f"icd10{year.value}en.xml",
            }
        elif year == Year.NHS_2016:
            return {
                "url": "scraped",
                "zip_filename": f"icd10_nhs_scraped_{self.timestamp}.zip",
                "xml_filename": f"icd10_nhs_scraped_{self.timestamp}.xml",
            }
        else:
            raise ValueError(f"Unsupported year: {year}")

    def download_zip(
        self,
        year: Year,
        force_download: bool = False,
    ) -> Path:
        """
        Ensure the ICD-10 ClaML ZIP file is available locally.
        """
        release_dir = Path(self.release_dir)
        release_dir.mkdir(parents=True, exist_ok=True)

        metadata = self.get_release_metadata(year)
        url = metadata["url"]
        zip_filename = metadata["zip_filename"]

        zip_path = release_dir / zip_filename

        if year != Year.NHS_2016 and (force_download or not zip_path.exists()):
            urllib.request.urlretrieve(url, zip_path)
        elif year == Year.NHS_2016:
            # download file if there aren't any previously-scraped or if forced
            # can't use zip_path as filename contains a timestamp``
            previous_scraped_files = list(release_dir.glob("icd10_nhs_scraped_*.zip"))
            last_scraped_zip = (
                sorted(previous_scraped_files, key=lambda f: f.stem, reverse=True)[0]
                if previous_scraped_files
                else None
            )
            if not force_download and last_scraped_zip and last_scraped_zip.exists():
                return last_scraped_zip
            # Scrape the NHS ICD-10 Class Browser and convert to ClaML
            chapters = scrape()
            xml_path = release_dir / metadata["xml_filename"]
            convert_chapters_to_claml(chapters, xml_path)
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.write(xml_path, arcname=metadata["xml_filename"])

        return zip_path

    def extract_xml_from_zip(
        self, zip_path: Path, year: Year, force_extract: bool = False
    ) -> Path:
        metadata = self.get_release_metadata(year)
        xml_filename = metadata["xml_filename"]
        xml_path = zip_path.parent / xml_filename

        if force_extract or not xml_path.exists():
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extract(xml_filename, xml_path.parent)

        return xml_path

    def download_release(
        self,
        year: Year,
        force_download: bool = False,
    ) -> Path:
        """
        Ensure the ICD-10 ClaML XML file is available locally.

        Downloads the ZIP if not already cached, then extracts it.
        Returns the path to the extracted XML file.
        """
        zip_path = self.download_zip(year, force_download)
        xml_path = self.extract_xml_from_zip(zip_path, year, force_download)
        return xml_path

    def download_latest_release(self, force_download=True):
        """Downloads the latest ICD-10 ClaML files from WHO and scrapes the NHS ICD-10 Class Browser."""
        xml_paths = []
        print("Downloading WHO ICD-10 ClaMLs")
        xml_paths.append(self.download_release(Year.WHO_2016, force_download))
        xml_paths.append(self.download_release(Year.WHO_2019, force_download))
        print("Scraping NHS ICD-10 Browser and converting to ClaML")
        xml_paths.append(self.download_release(Year.NHS_2016, force_download))

        combined_zip_path = (
            Path(self.release_dir) / f"icd10_combined_{self.timestamp}.zip"
        )
        with zipfile.ZipFile(combined_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for xml_path in xml_paths:
                zf.write(xml_path, arcname=xml_path.name)

        return combined_zip_path, {
            "release_name": f"icd10_combined_{self.timestamp}",
            "valid_from": self.timestamp,
            "filename": combined_zip_path.name,
            "file_metadata": {y.name: self.get_release_metadata(y) for y in Year},
        }
