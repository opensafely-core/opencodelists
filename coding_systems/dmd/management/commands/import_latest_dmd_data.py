import sys
from pathlib import Path

from django.core.management import BaseCommand

from coding_systems.dmd.import_data import DMDTrudDownloader, import_release
from coding_systems.versioning.models import CodingSystemRelease


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "release_dir", help="Path to local release directory to download raw data"
        )

    def handle(self, release_dir, **kwargs):
        downloader = DMDTrudDownloader(release_dir)
        metadata = downloader.get_latest_release_metadata()
        valid_from = metadata["valid_from"]
        release_name = f"{valid_from.year} {metadata['release']}"

        # bail if a Coding System Release already exists
        if CodingSystemRelease.objects.filter(
            coding_system="dmd",
            release_name=release_name,
            valid_from=valid_from,
        ).exists():
            self.stdout.write(
                f"A dm+d coding system release already exists for the latest release '{release_name}' and "
                f"valid from date {valid_from}.  If you want to force a re-import, use "
                "`manage.py import_coding_system_data`"
            )
            sys.exit(1)

        release_zipfile_path = Path(release_dir) / metadata["filename"]
        downloader.get_file(metadata["url"], release_zipfile_path)
        import_release(release_zipfile_path, release_name, valid_from)

        self.stdout.write(
            f"Imported release {release_name}, valid from {valid_from}\n"
            "\n*** APP RESTART REQUIRED ***\n"
            "Import complete; run `dokku ps:restart opencodelists` to restart the app"
        )
