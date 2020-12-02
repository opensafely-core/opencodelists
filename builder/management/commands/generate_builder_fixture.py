"""
Generate a JSON containing the context that is passed to the page by
builder.views.codelist, for use in testing frontend code.
"""

import json
from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, CommandError, call_command
from django.db import connections
from django.test.client import Client

from builder import actions
from codelists.search import do_search
from codelists.tests.factories import CodelistFactory
from coding_systems.snomedct.models import Concept
from opencodelists.tests.factories import UserFactory


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument("path", help="Path to write JSON file")

    def handle(self, path, **kwargs):
        set_up_db()

        fixtures_path = Path(
            settings.BASE_DIR, "coding_systems", "snomedct", "fixtures"
        )
        call_command("loaddata", fixtures_path / "core-model-components.json")
        call_command("loaddata", fixtures_path / "tennis-elbow.json")

        codelist = CodelistFactory()
        owner = UserFactory()
        draft = actions.create_draft(owner=owner, codelist=codelist)
        search_results = do_search(draft.coding_system, "elbow")
        actions.create_search(
            draft=draft, term="elbow", codes=search_results["all_codes"]
        )

        client = Client()
        client.force_login(owner)

        rsp = client.get(f"/builder/{draft.hash}/")
        data = {
            k: rsp.context[k]
            for k in [
                "searches",
                "filter",
                "tree_tables",
                "all_codes",
                "included_codes",
                "excluded_codes",
                "parent_map",
                "child_map",
                "code_to_term",
                "code_to_status",
                "is_editable",
                "update_url",
                "search_url",
            ]
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2)


def set_up_db():
    """Set up the in-memory database so that we can avoid clobbering existing data.

    Clear the cached database connection, set up connection to in-memory sqlite3
    database, and migrate."""

    databases = connections.databases
    assert databases["default"]["ENGINE"] == "django.db.backends.sqlite3"
    databases["default"]["NAME"] = ":memory:"
    del connections.databases
    connections.__init__(databases=databases)
    call_command("migrate")

    # This is a belt-and-braces check to ensure that the above hackery has worked.
    if Concept.objects.count() > 0:
        raise CommandError("Must be run against empty database")
