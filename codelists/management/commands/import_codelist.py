from django.core.management import BaseCommand, CommandError

from ...coding_system import CODING_SYSTEMS
from ...import_codelist import ImportCodelistError, import_codelist


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("publisher")
        parser.add_argument("codelist")
        parser.add_argument("coding_system", choices=CODING_SYSTEMS.keys())
        parser.add_argument("version_str")
        parser.add_argument("csv_path")

    def handle(
        self, publisher, codelist, coding_system, version_str, csv_path, **kwargs
    ):
        try:
            import_codelist(publisher, codelist, coding_system, version_str, csv_path)
        except ImportCodelistError as e:
            raise CommandError(str(e))
