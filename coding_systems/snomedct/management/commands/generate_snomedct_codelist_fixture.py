"""
Generate a CSV file for containing codes derived from the given definition fragments.
"""
import csv

from django.core.management import BaseCommand

from codelists.coding_systems import CODING_SYSTEMS
from codelists.definition import codes_from_query


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument("fragments", nargs="+", help="Definition fragments")
        parser.add_argument("--path", help="Path to write CSV file")

    def handle(self, path, fragments, **kwargs):
        coding_system = CODING_SYSTEMS["snomedct"]

        codes = sorted(codes_from_query(coding_system, fragments))

        code_to_name = coding_system.lookup_names(codes)

        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "name"])
            for code in codes:
                writer.writerow([code, code_to_name[code]])
