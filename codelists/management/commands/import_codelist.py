from django.core.management import BaseCommand, CommandError

from ...import_codelist import ImportCodelistError, import_codelist
from ...models import CODING_SYSTEMS


class Command(BaseCommand):
    def add_arguments(self, parser):
        coding_systems = [tpl[0] for tpl in CODING_SYSTEMS]

        parser.add_argument("publisher")
        parser.add_argument("codelist")
        parser.add_argument("coding_system", choices=coding_systems)
        parser.add_argument("version")
        parser.add_argument("csv_path")

    def handle(self, publisher, codelist, coding_system, version, csv_path, **kwargs):
        try:
            import_codelist(
                publisher, codelist, coding_system, version, csv_path,
            )
        except ImportCodelistError as e:
            raise CommandError(str(e))
