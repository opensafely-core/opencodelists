import sys

from django.core.management import BaseCommand, call_command

from coding_systems.versioning.models import (
    CodingSystemRelease,
    build_db_path,
    update_coding_system_database_connections,
)
from opencodelists import settings
from opencodelists.tests.fixtures import build_fixtures


class Command(BaseCommand):
    help = """Populates local opencodelists dbs with test fixture data:
           Loads the CodingSystemReleases needed for the snomed and dmd
           fixtures into the Core db (you will be prompted for consent
           to do this), deletes existing test coding system release dbs,
           creates new coding system release dbs, populates these with
           test fixture data, instantiates a universe of fixture
           objects, and creates a superuser. Running this command
           directly is not recommended, instead use `just
           build-dbs-for-local-development`"""

    def handle(self, *args, **options):
        if not settings.DEBUG:
            self.stderr.write(
                "This management command will not run in a production environment."
            )
            sys.exit(1)

        load_versioning_fixture_answer = input(
            "Running this command will load the CodingSystemReleases needed for the snomed and dmd test fixtures, into the Core db. Any local test coding system release dbs will then be deleted and recreated. Do you want to proceed? (Y/n)"
        )

        if load_versioning_fixture_answer == "n":
            return

        call_command(
            "loaddata",
            "coding_systems/versioning/fixtures/coding_system_releases.json",
        )

        self.stdout.write("Deleting local coding system release dbs...")
        for coding_system_release in CodingSystemRelease.objects.all():
            db_path = build_db_path(coding_system_release)
            if db_path.exists():
                db_path.unlink()
                self.stdout.write(f"{str(db_path)} has been deleted")

        self.stdout.write(
            "Migrating coding system release dbs and populating them with test fixture data"
        )

        update_coding_system_database_connections()

        # migrate snomedct test db and load test fixtures
        call_command("migrate", "snomedct", database="snomedct_test_20200101")

        call_command(
            "loaddata",
            "coding_systems/snomedct/fixtures/core-model-components.snomedct_test_20200101.json",
            database="snomedct_test_20200101",
        )

        call_command(
            "loaddata",
            "coding_systems/snomedct/fixtures/tennis-elbow.snomedct_test_20200101.json",
            database="snomedct_test_20200101",
        )

        call_command(
            "loaddata",
            "coding_systems/snomedct/fixtures/tennis-toe.snomedct_test_20200101.json",
            database="snomedct_test_20200101",
        )

        # migrate dmd test db and load test fixture
        call_command("migrate", "dmd", database="dmd_test_20200101")

        call_command(
            "loaddata",
            "coding_systems/dmd/fixtures/asthma-medication.dmd_test_20200101.json",
            database="dmd_test_20200101",
        )

        # migrate bnf test db and load test fixture
        call_command("migrate", "bnf", database="bnf_test_20200101")

        call_command(
            "loaddata",
            "coding_systems/bnf/fixtures/asthma.bnf_test_20200101.json",
            database="bnf_test_20200101",
        )

        # migrate icd10 test db and load test fixture
        call_command("migrate", "icd10", database="icd10_test_20200101")
        call_command(
            "loaddata",
            "coding_systems/icd10/fixtures/icd10.icd10_test_20200101.json",
            database="icd10_test_20200101",
        )

        # instantiate the test data universe
        build_fixtures()

        self.stdout.write(
            "Creating Django superuser; you will be prompted to create a password"
        )
        call_command(
            "createsuperuser",
            no_input=True,
            username="localdev",
            email="localdev@example.com",
        )

        self.stdout.write(
            "Local setup complete! You can now:\n"
            " - Log in as `localdev`\n"
            " - Search for 'arthritis', 'tennis', and 'elbow'\n"
            " - Build codelists with the concepts returned from these searches (see /opencodelists/opencodelists/tests/fixtures.py for more info)\n"
            " - View a BNF codelist, a minimal codelist, and a new-style SNOMED CT codelist"
        )
