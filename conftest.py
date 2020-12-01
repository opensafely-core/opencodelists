from pathlib import Path

import pytest
from django.conf import settings
from django.core.management import call_command

from codelists import actions
from codelists.tests.factories import CodelistFactory
from opencodelists.tests.fixtures import build_fixture, universe  # noqa

pytest.register_assert_rewrite("codelists.tests.views.assertions")
pytest.register_assert_rewrite("opencodelists.tests.assertions")


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass


@pytest.fixture(scope="function")
def tennis_elbow():
    fixtures_path = Path(settings.BASE_DIR, "coding_systems", "snomedct", "fixtures")
    call_command("loaddata", fixtures_path / "core-model-components.json")
    call_command("loaddata", fixtures_path / "tennis-elbow.json")

    with open(fixtures_path / "disorder-of-elbow.csv") as f:
        yield f.read()


@pytest.fixture(scope="function")
def tennis_elbow_codelist(tennis_elbow):
    return CodelistFactory(csv_data=tennis_elbow)


@pytest.fixture(scope="function")
def tennis_elbow_new_style_codelist(tennis_elbow_codelist):
    actions.convert_codelist_to_new_style(codelist=tennis_elbow_codelist)
    return tennis_elbow_codelist


organisation = build_fixture("organisation")
organisation_admin = build_fixture("organisation_admin")
organisation_user = build_fixture("organisation_user")
user_without_organisation = build_fixture("user_without_organisation")
old_style_codelist = build_fixture("old_style_codelist")
old_style_version = build_fixture("old_style_version")
new_style_codelist = build_fixture("new_style_codelist")
version_with_no_searches = build_fixture("version_with_no_searches")
version_with_some_searches = build_fixture("version_with_some_searches")
version_with_complete_searches = build_fixture("version_with_complete_searches")
new_style_version = build_fixture("new_style_version")
draft_codelist = build_fixture("draft_codelist")
draft_version = build_fixture("draft_version")
user_codelist = build_fixture("user_codelist")
user_version = build_fixture("user_version")
