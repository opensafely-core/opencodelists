import glob
import os
from importlib import import_module

from django.core.management import BaseCommand


def possible_modules():
    paths = glob.glob("mappings/**/import_data.py", recursive=True)
    mods = []
    for path in paths:
        head, _ = os.path.split(path)
        mods.append(head.replace(os.sep, "."))
    return mods


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("dataset", choices=possible_modules())
        parser.add_argument("release_dir")

    def handle(self, dataset, release_dir, **kwargs):
        mod = import_module(dataset + ".import_data")
        fn = getattr(mod, "import_data")
        fn(release_dir)
