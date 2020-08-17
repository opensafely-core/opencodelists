import time

from django.core.management import BaseCommand

from codelists.actions import _build_definition
from codelists.models import CodelistVersion


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--all", action="store_true", help="Generate definitions for all Versions"
        )

    def handle(self, **options):
        if options["all"]:
            versions = CodelistVersion.objects.all()
        else:
            versions = CodelistVersion.objects.filter(definition=None)

        exceptions = 0

        for i, version in enumerate(versions):
            error = " "
            url = version.codelist.get_absolute_url()

            start = time.time()

            try:
                version.definition = _build_definition(version)
            except Exception:
                exceptions += 1
                error = "x"
            else:
                version.save()

            taken = round(time.time() - start, 2)
            print(f" {i:3} | {version.pk:3} | {taken:6} | {error} | {url}")

        print(f"Exceptions: {exceptions}")
