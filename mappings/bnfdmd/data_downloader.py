import glob
import os
import re
import zipfile
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

import requests
import structlog
from bs4 import BeautifulSoup


logger = structlog.get_logger()


# spike modelled after coding_systems/base/trud_utils.py::TrudDownloader


class Downloader:
    def __init__(self, release_dir):
        self.url = "https://www.nhsbsa.nhs.uk"
        self.release_dir = release_dir

    def op_download(self):
        # taken from openprescribing/openprescribing/dmd/management/commands/fetch_bnf_snomed_mapping.py

        page_url = "https://www.nhsbsa.nhs.uk/prescription-data/understanding-our-data/bnf-snomed-mapping"
        filename_re = re.compile(
            r"^BNF Snomed Mapping data (?P<date>20\d{6})\.zip$", re.IGNORECASE
        )

        rsp = requests.get(page_url)
        rsp.raise_for_status()
        doc = BeautifulSoup(rsp.text, "html.parser")

        matches = []
        for a_tag in doc.find_all("a", href=True):
            url = urljoin(page_url, a_tag["href"])
            filename = Path(unquote(urlparse(url).path)).name
            match = filename_re.match(filename)
            if match:
                matches.append((match.group("date"), url, filename))

        if not matches:
            raise RuntimeError(f"Found no URLs matching {filename_re} at {page_url}")

        # Sort by release date and get the latest
        matches.sort()
        datestamp, url, filename = matches[-1]

        # release_date = datestamp[:4] + "_" + datestamp[4:6] + "_" + datestamp[6:]
        dir_path = self.release_dir  # os.path.join(
        # settings.PIPELINE_DATA_BASEDIR, "bnf_snomed_mapping", release_date
        # )
        zip_path = os.path.join(dir_path, filename)

        if glob.glob(os.path.join(dir_path, "*.xlsx")):
            return

        # mkdir_p(dir_path)

        rsp = requests.get(url, stream=True)
        rsp.raise_for_status()

        with open(zip_path, "wb") as f:
            for block in rsp.iter_content(32 * 1024):
                f.write(block)

        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(dir_path)

    def get_releases(self):
        # adapted from openprescribing/openprescribing/dmd/management/commands/fetch_bnf_snomed_mapping.py
        page_url = (
            f"{self.url}/prescription-data/understanding-our-data/bnf-snomed-mapping"
        )
        filename_re = re.compile(
            r"^BNF Snomed Mapping data (?P<date>20\d{6})\.zip$", re.IGNORECASE
        )

        rsp = requests.get(page_url)
        rsp.raise_for_status()
        doc = BeautifulSoup(rsp.text, "html.parser")

        matches = []
        for a_tag in doc.find_all("a", href=True):
            url = urljoin(page_url, a_tag["href"])
            filename = Path(unquote(urlparse(url).path)).name
            match = filename_re.match(filename)
            if match:
                matches.append((match.group("date"), url, filename))

        if not matches:
            raise RuntimeError(f"Found no URLs matching {filename_re} at {page_url}")

        # Sort by release date and get the latest
        matches.sort()

        return matches

    def get_latest_release(self):
        return self.get_releases()[0]

    def get_release_metadata(self, release):
        datestamp, url, filename = release
        datepat = re.compile(r"\w+ \d{4}")
        datefmt = "%B %Y"
        valid_from = datepat.search(url).group()
        valid_from = datetime.strptime(valid_from, datefmt)
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
        with requests.get(url, stream=True) as resp:
            resp.raise_for_status()
            with open(filepath, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
        logger.info("Download complete", download_filepath=filepath)
        logger.info("Starting unzip", download_filepath=filepath)
        with zipfile.ZipFile(filepath) as zf:
            zf.extractall(self.release_dir)
        logger.info("Unzipping complete", download_filepath=filepath)

    def download_latest_release(self):
        metadata = self.get_latest_release_metadata()

        if glob.glob(os.path.join(self.release_dir, metadata["filename"])):
            return

        local_download_filepath = Path(self.release_dir) / metadata["filename"]
        self.get_file(metadata["url"], local_download_filepath)

        return local_download_filepath, metadata
