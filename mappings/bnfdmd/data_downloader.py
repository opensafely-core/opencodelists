import re
from datetime import datetime
from pathlib import Path

import requests
import structlog
from lxml import html


logger = structlog.get_logger()


# spike modelled after coding_systems/base/trud_utils.py::TrudDownloader


class Downloader:
    def __init__(self, release_dir):
        self.url = "https://www.nhsbsa.nhs.uk"
        self.release_dir = release_dir

    def get_releases(self):
        resp = requests.get(
            f"{self.url}/prescription-data/understanding-our-data/bnf-snomed-mapping"
        )
        resp.raise_for_status()
        tree = html.fromstring(resp.content)

        datepat = re.compile(r"\w+ \d{4}")
        datefmt = "%B %Y"

        def parse_link_para(p):
            inner_text = p.text_content().replace("\xa0", " ")
            date_string = datepat.search(inner_text).group()
            valid_date = datetime.strptime(date_string, datefmt)
            href = None
            for e in p:
                if "href" in e.attrib:
                    href = e.get("href")
                    break
            if not href:
                raise ValueError(f"Unable to find url in {html.tostring(p)}")
            return {
                "valid_from": valid_date.date(),
                "archiveFileUrl": f"{self.url}{href}",
            }

        ziplinks = [
            parse_link_para(a.getparent())
            for a in tree.xpath("//body//a")
            if a.get("href").endswith(".zip")
        ]

        return sorted(ziplinks, key=lambda z: z["valid_from"], reverse=True)

    def get_latest_release(self):
        return self.get_releases()[0]

    def get_release_metadata(self, release):
        download_url = release["archiveFileUrl"]
        filename = download_url.split("/")[-1]
        release_name = filename.split("%20")[-1].replace(".zip", "")
        return {
            "release": release_name,
            "valid_from": release["valid_from"],
            "url": download_url,
            "filename": filename,
            "release_name": release_name,
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

    def download_latest_release(self):
        metadata = self.get_latest_release_metadata()

        # todo bail if release already loaded

        local_download_filepath = Path(self.release_dir) / metadata["filename"]
        self.get_file(metadata["url"], local_download_filepath)

        return local_download_filepath, metadata
