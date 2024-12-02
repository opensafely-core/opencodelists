from importlib import import_module

from django.core.management import BaseCommand

from mappings import mappings


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.description = "Import a coding system mapping"
        parser.add_argument("mapping", choices=mappings.keys(), help="Mapping name")
        parser.add_argument(
            "source",
            help=(
                "File or dir that defines the mapping, see import_data.py in "
                "the mapping's package to understand how it is used"
            ),
        )

    def handle(self, mapping, source, **kwargs):
        mapping_import_data_module = import_module(f"mappings.{mapping}.import_data")
        import_data = getattr(mapping_import_data_module , "import_data")
        import_data(source)
