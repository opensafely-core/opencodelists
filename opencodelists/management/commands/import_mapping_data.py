import importlib

from django.core.management import BaseCommand

from mappings import mappings


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("dataset", choices=mappings.keys())
        parser.add_argument("release_dir")

    def handle(self, dataset, release_dir, **kwargs):
        mod = importlib.import_module(f"mappings.{dataset}.import_data")
        fn = getattr(mod, "import_data")
        fn(release_dir)
