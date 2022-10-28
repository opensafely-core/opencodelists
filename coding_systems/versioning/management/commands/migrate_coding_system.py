import subprocess
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.management import BaseCommand
from django.db import DEFAULT_DB_ALIAS, transaction
from django.utils import timezone

from codelists.coding_systems import CODING_SYSTEMS
from coding_systems.versioning.models import CodingSystemVersion


class Command(BaseCommand):

    help = """
        Migrate coding systems to support Coding System versioning.
        See https://github.com/opensafely-core/opencodelists/issues/1379

        Extracts the tables for coding system(s) from the default database and loads each
        coding system into a new database, with the version "unknown".

        This is only intended to be run once.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--coding-systems",
            nargs="*",
            choices=CODING_SYSTEMS.keys(),
            default=CODING_SYSTEMS.keys(),
            help="Optional list of coding system ids to migrate",
        )
        parser.add_argument(
            "--force",
            "-f",
            action="store_true",
            help="Override existing initial version migration",
        )
        # Optional source db; this only exists so we can pass in a different db in tests
        parser.add_argument(
            "--source-db",
            type=Path,
            help="Path to the source database",
        )

    @transaction.atomic
    def handle(self, coding_systems, force, source_db, **kwargs):
        import_datetime = timezone.now()
        source_db = source_db or settings.DATABASES[DEFAULT_DB_ALIAS]["NAME"]

        for coding_system in coding_systems:
            # Check this coding system is migrate-able (i.e. it's a valid app)
            if coding_system not in apps.app_configs:
                self.stdout.write(f"{coding_system} is not an app, skipping.")
                continue

            # Create CodingSystemVersion for the initial "unknown" version or bail if one exists already
            if (
                force
                or not CodingSystemVersion.objects.filter(
                    coding_system=coding_system
                ).exists()
            ):
                coding_system_version, _ = CodingSystemVersion.objects.update_or_create(
                    coding_system=coding_system,
                    version="unknown",
                    import_ref="unknown",
                    defaults={
                        "valid_from": import_datetime,
                        "import_timestamp": import_datetime,
                    },
                )
            else:
                self.stdout.write(
                    f"CodingSystemVersion already exists for {coding_system}, skipping.\n"
                    "Run with --force to overwrite."
                )
                continue

            self.stdout.write(f"Migrating {coding_system} to new separate database")

            new_db_path = self.get_new_database_filepath(coding_system_version, force)

            self.load_data_to_new_database(coding_system, new_db_path, source_db)

    def get_new_database_filepath(self, coding_system_version, force):
        """
        Generate filepath for the new database and delete existing database file if necessary
        """
        db_name = coding_system_version.db_name
        new_db_path = (
            settings.CODING_SYSTEMS_DATABASE_DIR
            / coding_system_version.coding_system
            / f"{db_name}.sqlite3"
        )

        if new_db_path.exists() and force:
            self.stdout.write(f"Database {new_db_path} already exists, deleting...")
            new_db_path.unlink()

        if not new_db_path.exists():
            self.stdout.write(
                f"Database {new_db_path} does not exist and will be created"
            )

        return new_db_path

    def load_data_to_new_database(self, coding_system, new_db_path, source_db):
        """
        Dump all the coding_system tables from the default DB and load them into the new one
        """
        dump_file_dir = settings.DATABASE_DUMP_DIR
        dump_file_dir.mkdir(exist_ok=True, parents=True)

        for model in apps.get_app_config(coding_system).get_models():
            table_name = model._meta.db_table
            dump_file = dump_file_dir / f"{table_name}.dump.sql"
            self.stdout.write(f"Dumping table {table_name} to {dump_file}")
            with open(dump_file, "w") as outfile:
                subprocess.run(
                    [
                        "sqlite3",
                        f"{source_db}",
                        f".dump '{table_name}'",
                    ],
                    stdout=outfile,
                    check=True,
                )

            with open(dump_file) as infile:
                self.stdout.write(
                    f"Loading table {table_name} from {dump_file} to {new_db_path}"
                )
                subprocess.run(["sqlite3", str(new_db_path)], stdin=infile, check=True)
