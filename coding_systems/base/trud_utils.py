from datetime import date
from pathlib import Path

import requests
import structlog
from django.conf import settings

from coding_systems.versioning.models import CodingSystemRelease

logger = structlog.get_logger()


class TrudDownloader:
    """
    A downloader for items we obtain via TRUD (dm+d and SNOMED-CT).
    """

    # TRUD item number
    item_number = NotImplemented
    # A (compiled) regex to match release filenames for this TRUD item
    # Should include a named group for ?P<release> which identifies
    # the release from the filename, e.g.
    # re.compile(r"^uk_sct2cl_(?P<release>\d+\.\d+\.\d+)_20\d{12}Z\.zip$")
    # finds the release 35.5.0 from uk_sct2cl_35.5.0_20230215000001Z.zip
    release_regex = NotImplemented

    coding_system_id = NotImplemented

    def __init__(self, release_dir):
        self.url = f"https://isd.digital.nhs.uk/trud/api/v1/keys/{settings.TRUD_API_KEY}/items/{self.item_number}/releases"
        self.release_dir = release_dir

    def get_releases(self, latest=False):
        url = self.url + "?latest" if latest else self.url
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.json()["releases"]

    def get_latest_release(self):
        return self.get_releases(latest=True)[0]

    def get_latest_release_metadata(self):
        latest = self.get_latest_release()
        return self.get_release_metadata(latest)

    def get_release_metadata(self, release):
        filename = release["archiveFileName"]
        download_url = release["archiveFileUrl"]
        matches = self.release_regex.match(filename)
        if not matches:
            return {}
        matched_groups = matches.groupdict()
        release_metadata = {
            "release": matched_groups["release"],
            "valid_from": date.fromisoformat(release["releaseDate"]),
            "url": download_url,
            "filename": filename,
        }
        release_name = self.get_release_name_from_release_metadata(release_metadata)
        return {**release_metadata, "release_name": release_name}

    def get_release_name_from_release_metadata(self, metadata):
        """
        Build the release_name string from the parsed metadata retrieved from TRUD.

        By default this is the same release number/version parsed from the filename,
        but for some items (e.g. dm+d) it may include additional info such as the
        year.
        """
        return metadata["release"]

    def download_release(self, release_name, valid_from, latest):
        """
        Download a release that matches the specified release_name and valid_from values
        If latest=True, only fetch the latest release.
        """
        logger.info(
            "Attempting to download release from TRUD",
            release=release_name,
            valid_from=valid_from,
        )

        releases = self.get_releases(latest)
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

    def download_latest_release(self):
        metadata = self.get_latest_release_metadata()

        # bail if a Coding System Release already exists
        if CodingSystemRelease.objects.filter(
            coding_system=self.coding_system_id,
            release_name=metadata["release_name"],
            valid_from=metadata["valid_from"],
        ).exists():
            raise ValueError("Latest release already exists")

        local_download_filepath = Path(self.release_dir) / metadata["filename"]
        self.get_file(metadata["url"], local_download_filepath)

        return local_download_filepath, metadata

    def get_file(self, url, filepath):
        logger.info("Starting download", download_filepath=filepath)
        with requests.get(url, stream=True) as resp:
            resp.raise_for_status()
            with open(filepath, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
        logger.info("Download complete", download_filepath=filepath)
