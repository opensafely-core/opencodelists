"""
Generate a JSON containing the context that is passed to the page by
builder.views.codelist, for use in testing frontend code.
"""

import json
from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, CommandError, call_command
from django.test.client import Client

from builder import actions
from codelists.search import do_search
from coding_systems.snomedct.models import Concept
from opencodelists.tests.factories import UserFactory


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument("path", help="Path to write JSON file")

    def handle(self, path, **kwargs):
        if Concept.objects.count() > 0:
            raise CommandError("Must be run against empty database")

        fixtures_path = Path(
            settings.BASE_DIR, "coding_systems", "snomedct", "fixtures"
        )
        call_command("loaddata", fixtures_path / "core-model-components.json")
        call_command("loaddata", fixtures_path / "tennis-elbow.json")

        owner = UserFactory()
        cl = actions.create_codelist(
            owner=owner, name="Elbows", coding_system_id="snomedct"
        )
        search_results = do_search(cl.coding_system, "elbow")
        actions.create_search(
            codelist=cl, term="elbow", codes=search_results["all_codes"]
        )

        client = Client()
        client.force_login(owner)

        rsp = client.get(f"/builder/{owner.username}/{cl.slug}/")
        data = {
            k: rsp.context[k]
            for k in [
                "searches",
                "filter",
                "tree_tables",
                "included_codes",
                "excluded_codes",
                "displayed_codes",
                "parent_map",
                "child_map",
                "code_to_term",
                "code_to_status",
                "is_editable",
                "update_url",
                "search_url",
                "download_url",
            ]
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2)
