import sys
from importlib import import_module

from django.core.management import BaseCommand


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "coding_system_id",
            help="Coding system to import",
            choices=["dmd", "snomedct"],
        )
        parser.add_argument(
            "release_dir", help="Path to local release directory to download raw data"
        )

    def handle(self, coding_system_id, release_dir, **kwargs):
        downloader_module_path = f"coding_systems.{coding_system_id}.data_downloader"
        downloader_module = import_module(downloader_module_path)
        downloader_cls = downloader_module.Downloader

        import_module_path = f"coding_systems.{coding_system_id}.import_data"
        importer_module = import_module(import_module_path)
        import_fn = importer_module.import_release

        downloader = downloader_cls(release_dir)
        try:
            release_zipfile_path, metadata = downloader.download_latest_release()
        except ValueError:
            metadata = downloader.get_latest_release_metadata()
            self.stdout.write(
                f"A {coding_system_id} coding system release already exists for the latest release "
                f"({metadata['release']}) and valid from date ({metadata['valid_from']}). If you "
                "want to force a re-import, use `manage.py import_coding_system_data`"
            )
            sys.exit(1)

        release_name = metadata["release_name"]
        valid_from = metadata["valid_from"]
        import_fn(release_zipfile_path, release_name, valid_from)

        self.stdout.write(
            f"Imported {coding_system_id} release {release_name}, valid from {valid_from}\n"
            "\n*** APP RESTART REQUIRED ***\n"
            "Import complete; run `dokku ps:restart opencodelists` to restart the app"
        )
