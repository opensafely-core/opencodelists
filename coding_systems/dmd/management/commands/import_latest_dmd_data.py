import sys

from django.core.management import BaseCommand

from coding_systems.dmd.import_data import DMDTrudDownloader, import_release


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "release_dir", help="Path to local release directory to download raw data"
        )

    def handle(self, release_dir, **kwargs):
        downloader = DMDTrudDownloader(release_dir)
        try:
            release_zipfile_path, metadata = downloader.download_latest_release()
        except ValueError:
            metadata = downloader.get_latest_release_metadata()
            self.stdout.write(
                "A dm+d coding system release already exists for the latest release "
                f"({metadata['release']}) and valid from date ({metadata['valid_from']}). If you "
                "want to force a re-import, use `manage.py import_coding_system_data`"
            )
            sys.exit(1)

        release_name = metadata["release_name"]
        valid_from = metadata["valid_from"]
        import_release(release_zipfile_path, release_name, valid_from)

        self.stdout.write(
            f"Imported release {release_name}, valid from {valid_from}\n"
            "\n*** APP RESTART REQUIRED ***\n"
            "Import complete; run `dokku ps:restart opencodelists` to restart the app"
        )
