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

from codelists.actions import export_to_builder
from coding_systems.snomedct.models import Concept
from opencodelists.tests.fixtures import build_fixtures


class Command(BaseCommand):
    help = __doc__

    def handle(self, **kwargs):
        set_up_db()

        snomed_fixtures_path = Path(
            settings.BASE_DIR, "coding_systems", "snomedct", "fixtures"
        )
        call_command("loaddata", snomed_fixtures_path / "core-model-components.json")
        call_command("loaddata", snomed_fixtures_path / "tennis-elbow.json")

        fixtures = build_fixtures()

        organisation_user = fixtures["organisation_user"]
        client = Client()
        client.force_login(organisation_user)

        for version_key in [
            "version_with_no_searches",
            "version_with_some_searches",
            "version_with_complete_searches",
            "version_from_scratch",
        ]:
            version = fixtures[version_key]
            if version_key != "version_from_scratch":
                draft = export_to_builder(version=version, author=organisation_user)

            rsp = client.get(draft.get_builder_draft_url())
            data = {
                context_key: rsp.context[context_key]
                for context_key in [
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
                    "versions",
                    "metadata",
                ]
            }

            # Ensure that all fields are sorted, to allow for meaningful diffs should
            # the data change.
            data["all_codes"] = sorted(data["all_codes"])
            data["included_codes"] = sorted(data["included_codes"])
            data["excluded_codes"] = sorted(data["excluded_codes"])
            data["parent_map"] = {
                code: sorted(parents)
                for code, parents in sorted(data["parent_map"].items())
            }
            data["child_map"] = {
                code: sorted(children)
                for code, children in sorted(data["child_map"].items())
            }
            data["code_to_term"] = dict(sorted(data["code_to_term"].items()))
            data["code_to_status"] = dict(sorted(data["code_to_status"].items()))

            js_fixtures_path = Path(
                settings.BASE_DIR, "static", "test", "js", "fixtures"
            )

            with open(js_fixtures_path / f"{version_key}.json", "w") as f:
                json.dump(data, f, indent=2)


def set_up_db():
    """Set up the in-memory database so that we can avoid clobbering existing data.

    Clear the cached database connection, set up connection to in-memory sqlite3
    database, and migrate."""

    databases = connections.databases
    assert databases["default"]["ENGINE"] == "django.db.backends.sqlite3"
    databases["default"]["NAME"] = ":memory:"
    del connections.settings
    connections.__init__(settings=databases)
    call_command("migrate")

    # This is a belt-and-braces check to ensure that the above hackery has worked.
    if Concept.objects.count() > 0:
        raise CommandError("Must be run against empty database")
