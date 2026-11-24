import logging
from datetime import datetime
from pathlib import Path

from coding_systems.bnf.fetch_data import (
    download_csv,
    get_release_metadata,
    parse_name,
)


log = logging.getLogger(__name__)


class Downloader:
    def __init__(self, release_dir):
        self.release_dir = Path(release_dir)

    def download_latest_release(self):
        if not self.release_dir.is_dir():
            raise FileNotFoundError(
                f"BNF CSV directory does not exist or is not a directory: {self.release_dir}"
            )

        # Find the latest local release file
        existing_files = self.release_dir.glob("*.csv")
        csv_path = max(
            existing_files,
            default=None,
            key=lambda file: parse_name(file.name),
        )

        odp_response = get_release_metadata()

        # Identify the latest release using the release date and version
        # encoded in each resource's name, rather than relying on
        # the order of resources returned by the ODP API.
        latest = max(
            odp_response["result"]["resources"],
            key=lambda resource: parse_name(resource["name"]),
        )

        date, version = parse_name(latest["name"])
        valid_from = datetime.strptime(date, "%Y%m").date()
        release_name = f"{version} ({valid_from})"
        filename = f"bnf_code_current_{date}_version_{version}.csv"
        url = latest["url"]

        metadata = {
            "release": release_name,
            "release_name": release_name,
            "valid_from": valid_from,
            "import_ref": filename,
        }

        # Check whether the latest local CSV matches the latest ODP release.
        if csv_path is not None:
            csv_date, csv_version = parse_name(csv_path.name)

            if csv_date == date and csv_version == version:
                log.info(
                    "Latest BNF release CSV file already exists locally: %s",
                    csv_path,
                )
                return csv_path, metadata

        log.info("New BNF release available: %s.", latest["name"])
        release_csv_path = download_csv(
            date,
            version,
            url,
            self.release_dir,
        )

        return release_csv_path, metadata
