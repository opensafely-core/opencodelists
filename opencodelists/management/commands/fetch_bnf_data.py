from pathlib import Path

from django.core.management import BaseCommand

from coding_systems.bnf.fetch_data import fetch_data


class Command(BaseCommand):
    help = "Fetch the latest BNF coding system CSV from the NHSBSA ODP API."

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_directory",
            help="Path to the BNF data storage directory",
        )

    def handle(self, csv_directory, **kwargs):
        csv_download_path = fetch_data(Path(csv_directory))

        if csv_download_path is None:
            self.stdout.write(
                "We already have the latest BNF coding system release CSV. No further action needed."
            )
        else:
            self.stdout.write(
                f"Downloaded new BNF coding system release CSV to {csv_download_path}"
            )
