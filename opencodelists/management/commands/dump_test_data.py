from django.core.management import BaseCommand, call_command


class Command(BaseCommand):
    def handle(self):
        # ./manage.py migrate
        # call_command("migrate") # we don't need this as the just recipe handles the initial migration

        # ./manage.py loaddata coding_systems/versioning/fixtures/coding_system_releases.json
        call_command(
            "loaddata", "coding_systems/versioning/fixtures/coding_system_releases.json"
        )

        # ./manage.py migrate snomedct --database snomedct_test_20200101
        call_command("migrate", "snomedct", database="snomedct_test_20200101")

        # ./manage.py loaddata --database snomedct_test_20200101 coding_systems/snomedct/fixtures/core-model-components.snomedct_test_20200101.json
        call_command(
            "loaddata",
            "coding_systems/snomedct/fixtures/core-model-components.snomedct_test_20200101.json",
            database="snomedct_test_20200101",
        )

        # ./manage.py loaddata --database snomedct_test_20200101 coding_systems/snomedct/fixtures/tennis-elbow.snomedct_test_20200101.json
        call_command(
            "loaddata",
            "test_20200101 coding_systems/snomedct/fixtures/tennis-elbow.snomedct_test_20200101.json",
            database="snomedct_test_20200101",
        )

        # ./manage.py loaddata --database snomedct_test_20200101 coding_systems/snomedct/fixtures/tennis-toe.snomedct_test_20200101.json
        call_command(
            "loaddata",
            "test_20200101 coding_systems/snomedct/fixtures/tennis-toe.snomedct_test_20200101.json",
            database="snomedct_test_20200101",
        )

        # ./manage.py migrate bnf --database bnf_test_20200101
        call_command("migrate", "bnf", database="bnf_test_20200101")

        # ... hopefully you get the idea from here!

        # you'll also need to build the fixtures to populate these databases with the fixture objects
