import glob
import os
import sys
from importlib import import_module

from django.core.management import BaseCommand


def iter_possible_modules():
    paths = glob.glob("**/import_data.py", recursive=True)

    for path in paths:
        head, _ = os.path.split(path)
        yield head.replace(os.sep, ".")


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("dataset")
        parser.add_argument("release_dir")

    def handle(self, dataset, release_dir, **kwargs):
        try:
            mod = import_module(dataset + ".import_data")
        except ModuleNotFoundError:
            print(f"Could not find an 'import_data.py' module at path '{dataset}'")
            print("Maybe you meant one of these module paths?")

            possibilities = list(iter_possible_modules())
            for possibility in possibilities:
                print(possibility)

            sys.exit(1)

        fn = getattr(mod, "import_data")
        fn(release_dir)
