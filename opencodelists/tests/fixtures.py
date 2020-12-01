"""This module contains fixtures to be used in all apps.

One of the design goals of the project is that there should be a limited and controlled
number of states that objects can be ing  This is achieved by requiring (through
convention) that the only way to alter the state of an object is by calling a function
in one of the actions.py modules.

As such, test fixtures should only be created through invoking those actions.

However, this can make testing fiddly, since for instance to create a CodelistVersion in
a given state you might need to have an Organisation, a User, a Codelist, and other
CodelistVersions.  The approach we have taken is to build a "universe" of test objects
once, and then to pull out members of that universe as and when we need them.

This module contains some Cleverness, through use of locals() and dynamically generating
pytest fixtures.  This is acceptable Cleverness, because it should not leak out of the
module, and users of the module do not need to understand in detail how it works.
"""

import csv
from pathlib import Path

import pytest
from django.conf import settings
from django.core.management import call_command

from builder.actions import create_search, save, update_code_statuses
from codelists.actions import (
    create_codelist,
    create_codelist_from_scratch,
    create_codelist_with_codes,
    create_version,
    export_to_builder,
)
from codelists.coding_systems import CODING_SYSTEMS
from codelists.search import do_search
from opencodelists.actions import (
    add_user_to_organisation,
    create_organisation,
    create_user,
    make_user_admin_for_organisation,
)

# The following fixtures are available.  See comments in build_fixtures() for exactly
# what each fixture returns.
AVAILABLE_FIXTURES = {
    "organisation",
    "organisation_admin",
    "organisation_user",
    "user_without_organisation",
    "old_style_codelist",
    "old_style_version",
    "new_style_codelist",
    "version_with_no_searches",
    "version_with_some_searches",
    "version_with_complete_searches",
    "new_style_version",
    "draft_codelist",
    "draft_version",
    "user_codelist",
    "user_version",
}

SNOMED_FIXTURES_PATH = Path(settings.BASE_DIR, "coding_systems", "snomedct", "fixtures")


@pytest.fixture(scope="session")
def universe(django_db_setup, django_db_blocker):
    """Create universe of fixture objects.

    This fixture will be loaded exactly once per session.  It is not expected that it is
    used directly, but instead it is a dependency of the fixtures created by
    build_fixtures below.
    """
    with django_db_blocker.unblock():
        # load enough of the SNOMED hierarchy to be useful
        call_command("loaddata", SNOMED_FIXTURES_PATH / "core-model-components.json")
        call_command("loaddata", SNOMED_FIXTURES_PATH / "tennis-elbow.json")

        return build_fixtures()


def build_fixtures():
    """Create fixture objects.

    Returns a dict of locals(), mapping a key in AVAILABLE_FIXTURES to the fixture
    object.
    """

    # organisation
    # - has two users:
    #   - organisation_admin
    #   - organisation_user
    # - has three codelists:
    #   - old_style_codelist
    #   - new_style_codelist
    #   - draft_codelist
    organisation = create_organisation(name="Test University", url="https://test.ac.uk")

    # organisation_admin
    # - is admin for organisation
    organisation_admin = create_user(
        username="alice", name="Alice", email="alice@test.ac.uk", is_active=True
    )
    add_user_to_organisation(
        user=organisation_admin, organisation=organisation, date_joined="2020-02-29"
    )
    make_user_admin_for_organisation(user=organisation_admin, organisation=organisation)

    # organisation_user
    # - is non-admin for organisation
    # - is editing draft_version
    # - has one codelist:
    #   - user_codelist
    organisation_user = create_user(
        username="bob", name="Bob", email="bob@test.ac.uk", is_active=True
    )
    add_user_to_organisation(
        user=organisation_user, organisation=organisation, date_joined="2020-02-29"
    )

    # user_without_organisation
    # - does not belong to an organisation
    # - has no codelists
    user_without_organisation = create_user(
        username="charlie",
        name="Charlie",
        email="charlie@example.co.uk",
        is_active=True,
    )

    # old_style_codelist
    # - owned by organisation
    # - has one version:
    #   - old_style_version
    old_style_codelist = create_codelist(
        owner=organisation,
        name="Old-style Codelist",
        coding_system_id="snomedct",
        description="What this is",
        methodology="How we did it",
        csv_data=load_csv_data("disorder-of-elbow-excl-arthritis.csv"),
    )

    # old_style_version
    # - belongs to old_style_codelist
    old_style_version = create_version(
        codelist=old_style_codelist, csv_data=load_csv_data("disorder-of-elbow.csv")
    )

    # new_style_codelist
    # - belongs to organisation
    # - has four versions:
    #   - version_with_no_searches
    #   - version_with_some_searches
    #   - version_with_complete_searches
    new_style_codelist = create_codelist_with_codes(
        owner=organisation,
        name="New-style Codelist",
        coding_system_id="snomedct",
        codes=load_codes_from_csv("disorder-of-elbow-excl-arthritis.csv"),
    )

    # version_with_no_searches
    # - belongs to new_style_codelist
    # - has no searches
    version_with_no_searches = new_style_codelist.versions.get()

    # version_with_some_searches
    # - belongs to new_style_codelist
    # - has some searches, but not all codes covered
    version_with_some_searches = export_to_builder(
        version=version_with_no_searches, owner=organisation_user
    )
    create_search(
        draft=version_with_some_searches,
        term="arthritis",
        codes=codes_for_search_term("arthritis"),
    )
    update_code_statuses(
        draft=version_with_some_searches,
        updates=[("439656005", "+")],  # include "Disorder of elbow"
    )
    update_code_statuses(
        draft=version_with_some_searches,
        updates=[("3723001", "-")],  # exclude "Arthritis"
    )
    save(draft=version_with_some_searches)

    # version_with_complete_searches
    # - belongs to new_style_codelist
    # - has some searches, and all codes covered
    version_with_complete_searches = export_to_builder(
        version=version_with_some_searches, owner=organisation_user
    )
    create_search(
        draft=version_with_complete_searches,
        term="elbow",
        codes=codes_for_search_term("elbow"),
    )
    update_code_statuses(
        draft=version_with_complete_searches,
        updates=[("116309007", "-")],  # exclude "Finding of elbow region"
    )
    save(draft=version_with_complete_searches)

    # new_style_version
    # - an alias for version_with_some_searches
    new_style_version = version_with_some_searches

    # draft_codelist
    # - belongs to organisation
    # - has single version, being edited:
    #   - draft_version
    draft_codelist = create_codelist_from_scratch(
        owner=organisation,
        name="Draft Codelist",
        coding_system_id="snomedct",
        draft_owner=organisation_user,
    )

    # draft_version
    # - belongs to draft_codelist
    # - being edited by organisation_user
    draft_version = draft_codelist.versions.get()

    # user_codelist
    # - belongs to organisation_user
    # - has one version:
    #   - user_version
    user_codelist = create_codelist_with_codes(
        owner=organisation_user,
        name="User-owned Codelist",
        coding_system_id="snomedct",
        codes=load_codes_from_csv("disorder-of-elbow-excl-arthritis.csv"),
    )

    # user_version
    # - belongs to user_codelist
    user_version = user_codelist.versions.get()

    assert set(locals()) == AVAILABLE_FIXTURES
    return locals()


def load_csv_data(filename):
    """Return CSV data in given filename."""

    with open(SNOMED_FIXTURES_PATH / filename) as f:
        return f.read()


def load_codes_from_csv(filename):
    """Return codes in CSV file at given filename."""

    with open(SNOMED_FIXTURES_PATH / filename) as f:
        rows = list(csv.reader(f))

    return [row[0] for row in rows[1:]]


def codes_for_search_term(term):
    """Return codes matching search term."""

    coding_system = CODING_SYSTEMS["snomedct"]
    return do_search(coding_system, term)["all_codes"]


# Create each fixture in the module scope.
for fixture_name in AVAILABLE_FIXTURES:

    def build_fixture(fixture_name):
        """Build a fixture function."""

        def fixture(universe):
            """The actual pytest fixture.

            Finds the member of the universe with the given name, reloads it from the
            database, and returns it.
            """
            obj = universe[fixture_name]
            obj.refresh_from_db()
            return obj

        return fixture

    # Update the module's locals with the fixture's name.  This lets us do:
    #
    #   from opencodelists.tests.fixtures import *
    #
    # in conftest.py.
    locals()[fixture_name] = pytest.fixture(scope="function")(
        build_fixture(fixture_name)
    )
