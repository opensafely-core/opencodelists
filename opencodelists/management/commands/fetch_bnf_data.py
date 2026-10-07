from django.core.management import BaseCommand

from coding_systems.bnf.fetch_data import fetch_data


class Command(BaseCommand):
    help = "Fetch the latest BNF coding system CSV from the NHSBSA ODP API."

    def add_arguments(self, parser):
        parser.add_argument(
            "directory",
            help="Path to the BNF data storage directory",
        )

    def handle(self, directory, **kwargs):
        downloaded_path = fetch_data(directory)

        if downloaded_path is None:
            self.stdout.write(
                "We already have the latest BNF coding system release CSV. No further action needed."
            )
        else:
            self.stdout.write(
                f"Downloaded new BNF coding system release CSV to {downloaded_path}"
            )
