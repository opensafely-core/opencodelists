from importlib import import_module

from django.core.management import BaseCommand


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("dataset")
        parser.add_argument("release_dir")

    def handle(self, dataset, release_dir, **kwargs):
        mod = import_module(dataset + ".import_data")
        fn = getattr(mod, "import_data")
        fn(release_dir)
