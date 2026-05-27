"""
Apply either a specific, or all pending migrations for the `icd10` app to every release database
"""

from typing import Any

from django.core.management import BaseCommand, call_command
from django.core.management.base import CommandParser

from coding_systems.versioning.models import (
    CodingSystemRelease,
    update_coding_system_database_connections,
)


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("migration_name", nargs="?")

    def handle(self, *args: Any, **options: Any) -> str | None:
        update_coding_system_database_connections()
        for release in CodingSystemRelease.objects.filter(coding_system="icd10"):
            call_command(
                "migrate",
                "icd10",
                "--database",
                release.database_alias,
                "--fake-initial",
            )
