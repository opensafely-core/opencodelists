import glob
import os
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

import requests
import structlog
from bs4 import BeautifulSoup


logger = structlog.get_logger()


# modelled after coding_systems/base/trud_utils.py::TrudDownloader @ 979d995


class Downloader:
    def __init__(self, release_dir):
        self.url = "https://www.nhsbsa.nhs.uk/prescription-data/understanding-our-data/bnf-snomed-mapping"
        self.release_dir = release_dir

    def get_releases(self):
        # adapted from OpenPrescribing:
        # https://github.com/ebmdatalab/openprescribing/blob/main/openprescribing/dmd/management/commands/fetch_bnf_snomed_mapping.py
        filename_re = re.compile(
            r"^BNF Snomed Mapping data (?P<date>20\d{6})\.zip$", re.IGNORECASE
        )
        datepat = re.compile(r"\w+ \d{4}")
        datefmt = "%B %Y"

        rsp = requests.get(self.url)
        rsp.raise_for_status()
        doc = BeautifulSoup(rsp.text, "html.parser")

        matches = []
        for a_tag in doc.find_all("a", href=True):
            if a_tag.text.startswith("\xa0"):
                continue
            url = urljoin(self.url, a_tag["href"])
            filename = Path(unquote(urlparse(url).path)).name
            match = filename_re.match(filename)
            if match:
                inner_text = a_tag.text
                while not (
                    valid_from := datepat.search(inner_text.replace("\xa0", " "))
                ):
                    # sometimes "valid from" inner text is across adjacent elements
                    if a_tag.next_sibling:
                        inner_text += a_tag.next_sibling.text
                    elif a_tag.previous_sibling:
                        inner_text = a_tag.previous_sibling.text + inner_text
                valid_from = datetime.strptime(valid_from.group(), datefmt)
                matches.append((match.group("date"), url, filename, valid_from))

        if not matches:
            raise RuntimeError(f"Found no URLs matching {filename_re} at {self.url}")

        # Sort by release date and get the latest
        matches.sort()

        return matches

    def get_latest_release(self):
        return self.get_releases()[-1]

    def get_release_metadata(self, release):
        datestamp, url, filename, valid_from = release

        return {
            "release": datestamp,
            "valid_from": valid_from,
            "url": url,
            "filename": filename,
            "release_name": datestamp,
        }

    def get_latest_release_metadata(self):
        latest = self.get_latest_release()
        return self.get_release_metadata(latest)

    def download_release(self, release_name, valid_from):
        """
        Download a release that matches the specified release_name and valid_from values
        """
        logger.info(
            "Attempting to download release from NHS BSA",
            release=release_name,
            valid_from=valid_from,
        )

        releases = self.get_releases()
        release_metadata = (self.get_release_metadata(release) for release in releases)

        match_found = False
        for metadata in release_metadata:
            if (
                metadata.get("release_name") == release_name
                and metadata.get("valid_from") == valid_from
            ):
                match_found = True
                break

        if not match_found:
            raise ValueError(
                f"No matching release found for release {release_name}, valid from {valid_from}"
            )

        local_download_filepath = Path(self.release_dir) / metadata["filename"]
        self.get_file(metadata["url"], local_download_filepath)

        return local_download_filepath

    def get_file(self, url, filepath):
        logger.info("Starting download", download_filepath=filepath)
        if not filepath.parent.exists():
            filepath.parent.mkdir(parents=True)
        with requests.get(url, stream=True) as resp:
            resp.raise_for_status()
            with open(filepath, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
        logger.info("Download complete", download_filepath=filepath)

    def download_latest_release(self):
        metadata = self.get_latest_release_metadata()

        if glob.glob(os.path.join(self.release_dir, metadata["filename"])):
            raise ValueError("Latest release already exists")

        local_download_filepath = Path(self.release_dir) / metadata["filename"]
        self.get_file(metadata["url"], local_download_filepath)

        return local_download_filepath, metadata
