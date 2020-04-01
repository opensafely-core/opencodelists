from django.core.management import BaseCommand

from ...import_data import import_data


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("release_dir")

    def handle(self, release_dir, **kwargs):
        import_data(release_dir)
