"""This module contains fixtures to be used in all apps.

One of the design goals of the project is that there should be a limited and controlled
number of states that objects can be in.  This is achieved by requiring (through
convention) that the only way to alter the state of an object is by calling a function
in one of the actions.py modules.

As such, test fixtures should only be created through invoking those actions.

However, this can make testing fiddly, since for instance to create a CodelistVersion in
a given state you might need to have an Organisation, a User, a Codelist, and other
CodelistVersions.  The approach we have taken is to build a "universe" of test objects
once, and then to pull out members of that universe as and when we need them.

Since each fixture function needs to do the same thing (find the member of the universe
with the given name, reload it from the database, and return it) we use build_fixture()
to avoid excessive duplication.

We use a very small subset of the SNOMED hierarchy.  For details, see
coding_systems/snomedct/fixtures/README.

There are fixtures for CodelistVersions with two different lists of codes:

    A) disorder-of-elbow
    B) disorder-of-elbow-excl-arthritis

The fixtures also create searches for "arthritis", "tennis", and "elbow".

The concepts returned by these searches are shown below, along with which of the two
list of codes they belong two.

.. Arthritis (3723001)
A. └ Arthritis of elbow (439656005)
A.   └ Lateral epicondylitis (202855006)
.. Finding of elbow region (116309007)
AB ├ Disorder of elbow (128133004)
AB │ ├ Arthropathy of elbow (429554009)
A. │ │ └ Arthritis of elbow (439656005)
A. │ │   └ Lateral epicondylitis (202855006)
AB │ ├ Enthesopathy of elbow region (35185008)
AB │ │ └ Epicondylitis (73583000)
A. │ │   └ Lateral epicondylitis (202855006)
AB │ └ Soft tissue lesion of elbow region (239964003)
.. └ Finding of elbow joint (298869002)
AB   ├ Arthropathy of elbow (429554009)
A.   │ └ Arthritis of elbow (439656005)
A.   │   └ Lateral epicondylitis (202855006)
..   └ Elbow joint inflamed (298163003)
A.     └ Arthritis of elbow (439656005)
A.       └ Lateral epicondylitis (202855006)
.. Tennis toe (238484001)
AB (Epicondylitis &/or tennis elbow) or (golfers' elbow) (156659008) [inactive]
"""

import csv
from io import StringIO
from pathlib import Path

import pytest
from django.conf import settings
from django.core.management import call_command
from django.db.models import Model

from builder.actions import create_search, save, update_code_statuses
from codelists.actions import (
    add_collaborator,
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
    set_api_token,
)

SNOMED_FIXTURES_PATH = Path(settings.BASE_DIR, "coding_systems", "snomedct", "fixtures")


def build_fixture(fixture_name):
    """Build a fixture function that returns the fixture object with the given name."""

    def fixture(universe):
        """The actual pytest fixture.

        Finds the member of the universe with the given name, reloads it from the
        database if necessary, and returns it.
        """
        obj = universe[fixture_name]
        if isinstance(obj, Model):
            # Some fixtures (eg disorder_of_elbow_codes) are not instances of Django
            # models.
            obj.refresh_from_db()
        return obj

    # This docstring is used in the output of `pytest --fixtures`
    fixture.__doc__ = f"Return {fixture_name} from the universe fixture"
    return pytest.fixture(scope="function")(fixture)


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
        call_command("loaddata", SNOMED_FIXTURES_PATH / "tennis-toe.json")

        return build_fixtures()


def build_fixtures():
    """Create fixture objects.

    Returns a dict of locals(), mapping a fixture name to the fixture object.
    """

    # disorder_of_elbow_codes
    disorder_of_elbow_codes = load_codes_from_csv("disorder-of-elbow.csv")

    # disorder_of_elbow_excl_arthritis_codes
    disorder_of_elbow_excl_arthritis_codes = load_codes_from_csv(
        "disorder-of-elbow-excl-arthritis.csv"
    )

    # disorder_of_elbow_csv_data
    disorder_of_elbow_csv_data = load_csv_data("disorder-of-elbow.csv")

    # disorder_of_elbow_excl_arthritis_csv_data
    disorder_of_elbow_excl_arthritis_csv_data = load_csv_data(
        "disorder-of-elbow-excl-arthritis.csv"
    )

    # disorder_of_elbow_csv_data_no_header
    disorder_of_elbow_csv_data_no_header = load_csv_data_no_header(
        "disorder-of-elbow.csv"
    )

    # disorder_of_elbow_excl_arthritis_csv_data_no_header
    disorder_of_elbow_excl_arthritis_csv_data_no_header = load_csv_data_no_header(
        "disorder-of-elbow-excl-arthritis.csv"
    )

    # organisation
    # - has two users:
    #   - organisation_admin
    #   - organisation_user
    # - has three codelists:
    #   - old_style_codelist
    #   - new_style_codelist
    #   - codelist_from_scratch
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
    # - is editing version_from_scratch
    # - has one codelist:
    #   - user_codelist
    organisation_user = create_user(
        username="bob", name="Bob", email="bob@test.ac.uk", is_active=True
    )
    add_user_to_organisation(
        user=organisation_user, organisation=organisation, date_joined="2020-02-29"
    )
    set_api_token(user=organisation_user)

    # user
    # - an alias for organisation_user
    user = organisation_user

    # collaborator
    # - is collaborator on new_style_codelist
    collaborator = create_user(
        username="charlie",
        name="Charlie",
        email="charlie@example.co.uk",
        is_active=True,
    )

    # user_without_organisation
    # - does not belong to an organisation
    # - has no codelists
    user_without_organisation = create_user(
        username="dave",
        name="Dave",
        email="dave@example.co.uk",
        is_active=True,
    )
    set_api_token(user=user_without_organisation)

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
        csv_data=disorder_of_elbow_excl_arthritis_csv_data,
    )

    # old_style_version
    # - belongs to old_style_codelist
    # - includes Disorder of elbow
    old_style_version = create_version(
        codelist=old_style_codelist,
        csv_data=disorder_of_elbow_csv_data,
    )

    # Check that this version has the expected codes
    check_expected_codes(old_style_version, disorder_of_elbow_codes)

    # new_style_codelist
    # - belongs to organisation
    # - is collaborated on by collaborator
    # - has four versions:
    #   - version_with_no_searches
    #   - version_with_some_searches
    #   - version_with_complete_searches
    new_style_codelist = create_codelist_with_codes(
        owner=organisation,
        name="New-style Codelist",
        coding_system_id="snomedct",
        codes=disorder_of_elbow_excl_arthritis_codes,
    )

    # version_with_no_searches
    # - belongs to new_style_codelist
    # - has no searches
    # - includes Disorder of elbow, excludes Arthritis
    version_with_no_searches = new_style_codelist.versions.get()

    # Check that no code_objs are linked to searches
    assert not version_with_no_searches.code_objs.filter(results__isnull=False).exists()

    # Check that this version has the expected codes
    check_expected_codes(
        version_with_no_searches, disorder_of_elbow_excl_arthritis_codes
    )

    # version_with_excluded_codes
    # - an alias for version_with_no_searches
    version_with_excluded_codes = version_with_no_searches

    # version_with_some_searches
    # - belongs to new_style_codelist
    # - has some searches, but not all codes covered
    # - includes Disorder of elbow
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
    update_code_statuses(
        draft=version_with_some_searches,
        updates=[("439656005", "+")],  # include "Arthritis of elbow"
    )
    save(draft=version_with_some_searches)

    # Check that some code_objs are linked to searches and some are not
    assert version_with_some_searches.code_objs.filter(results__isnull=True).exists()
    assert version_with_some_searches.code_objs.filter(results__isnull=False).exists()

    # Check that this version has the expected codes
    check_expected_codes(version_with_some_searches, disorder_of_elbow_codes)

    # version_with_complete_searches
    # - belongs to new_style_codelist
    # - has some searches, and all codes covered
    # - includes Disorder of elbow
    version_with_complete_searches = export_to_builder(
        version=version_with_some_searches, owner=organisation_user
    )
    create_search(
        draft=version_with_complete_searches,
        term="tennis",
        codes=codes_for_search_term("tennis"),
    )
    update_code_statuses(
        draft=version_with_complete_searches,
        updates=[("238484001", "-")],  # exclude "Tennis toe"
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
    update_code_statuses(
        draft=version_with_complete_searches,
        updates=[("156659008", "+")],  # include "(Epicondylitis &/or tennis elbow) ..."
    )
    # This search does not find any new codes, but we need a search with a code for
    # tests.
    create_search(
        draft=version_with_complete_searches,
        code="439656005",
        codes=codes_for_search_code("439656005"),
    )
    save(draft=version_with_complete_searches)

    # Check that all code_objs are linked to searches
    assert not version_with_complete_searches.code_objs.filter(
        results__isnull=True
    ).exists()

    # Check that this version has the expected codes
    check_expected_codes(version_with_complete_searches, disorder_of_elbow_codes)

    # codelist_with_collaborator
    # - an alias for new_style_codelist
    codelist_with_collaborator = new_style_codelist
    add_collaborator(codelist=codelist_with_collaborator, collaborator=collaborator)

    # codelist_from_scratch
    # - belongs to organisation
    # - has single version, being edited:
    #   - version_from_scratch
    codelist_from_scratch = create_codelist_from_scratch(
        owner=organisation,
        name="Codelist From Scratch",
        coding_system_id="snomedct",
        draft_owner=organisation_user,
    )

    # version_from_scratch
    # - belongs to codelist_from_scratch
    # - being edited by organisation_user
    version_from_scratch = codelist_from_scratch.versions.get()

    # Check that this version has no codes
    assert version_from_scratch.codes == ()

    # user_codelist
    # - belongs to organisation_user
    # - has one version:
    #   - user_version
    user_codelist = create_codelist_with_codes(
        owner=organisation_user,
        name="User-owned Codelist",
        coding_system_id="snomedct",
        codes=disorder_of_elbow_excl_arthritis_codes,
    )

    # user_version
    # - belongs to user_codelist
    user_version = user_codelist.versions.get()

    return locals()


def load_csv_data(filename):
    """Return CSV data in given filename."""

    with open(SNOMED_FIXTURES_PATH / filename) as f:
        return f.read()


def load_csv_data_no_header(filename):
    """Return CSV data in given filename, dropping header."""

    with open(SNOMED_FIXTURES_PATH / filename) as f:
        rows = list(csv.reader(f))[1:]

    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerows(rows)
    return buffer.getvalue()


def load_codes_from_csv(filename):
    """Return codes in CSV file at given filename."""

    with open(SNOMED_FIXTURES_PATH / filename) as f:
        rows = list(csv.reader(f))

    return [row[0] for row in rows[1:]]


def codes_for_search_term(term):
    """Return codes matching search term."""

    coding_system = CODING_SYSTEMS["snomedct"]
    return do_search(coding_system, term=term)["all_codes"]


def codes_for_search_code(code):
    """Return codes matching search code."""

    coding_system = CODING_SYSTEMS["snomedct"]
    return do_search(coding_system, code=code)["all_codes"]


def check_expected_codes(version, codes):
    assert sorted(version.codes) == sorted(codes)


disorder_of_elbow_codes = build_fixture("disorder_of_elbow_codes")
disorder_of_elbow_excl_arthritis_codes = build_fixture(
    "disorder_of_elbow_excl_arthritis_codes"
)
disorder_of_elbow_csv_data = build_fixture("disorder_of_elbow_csv_data")
disorder_of_elbow_excl_arthritis_csv_data = build_fixture(
    "disorder_of_elbow_excl_arthritis_csv_data"
)
disorder_of_elbow_csv_data_no_header = build_fixture(
    "disorder_of_elbow_csv_data_no_header"
)
disorder_of_elbow_excl_arthritis_csv_data_no_header = build_fixture(
    "disorder_of_elbow_excl_arthritis_csv_data_no_header"
)
organisation = build_fixture("organisation")
organisation_admin = build_fixture("organisation_admin")
organisation_user = build_fixture("organisation_user")
collaborator = build_fixture("collaborator")
user_without_organisation = build_fixture("user_without_organisation")
user = build_fixture("user")
old_style_codelist = build_fixture("old_style_codelist")
old_style_version = build_fixture("old_style_version")
new_style_codelist = build_fixture("new_style_codelist")
version_with_no_searches = build_fixture("version_with_no_searches")
version_with_some_searches = build_fixture("version_with_some_searches")
version_with_complete_searches = build_fixture("version_with_complete_searches")
version_with_excluded_codes = build_fixture("version_with_excluded_codes")
codelist_with_collaborator = build_fixture("codelist_with_collaborator")
codelist_from_scratch = build_fixture("codelist_from_scratch")
version_from_scratch = build_fixture("version_from_scratch")
user_codelist = build_fixture("user_codelist")
user_version = build_fixture("user_version")


# These extra fixtures make modifications to those built in build_fixtures
@pytest.fixture(scope="function")
def draft_with_no_searches(version_with_no_searches, organisation_user):
    return export_to_builder(version=version_with_no_searches, owner=organisation_user)


@pytest.fixture(scope="function")
def draft_with_some_searches(version_with_some_searches, organisation_user):
    return export_to_builder(
        version=version_with_some_searches, owner=organisation_user
    )


@pytest.fixture(scope="function")
def draft_with_complete_searches(version_with_complete_searches, organisation_user):
    return export_to_builder(
        version=version_with_complete_searches, owner=organisation_user
    )


# This is a parameterized fixture.  When used in a test, the test will be run once for
# each of version_with_no_searches, version_with_some_searches,
# version_with_complete_searches.
@pytest.fixture(
    scope="function",
    params=[
        "version_with_no_searches",
        "version_with_some_searches",
        "version_with_complete_searches",
    ],
)
def new_style_version(universe, request):
    version = universe[request.param]
    version.refresh_from_db()
    return version


@pytest.fixture
def icd10_data():
    path = Path(settings.BASE_DIR, "coding_systems", "icd10", "fixtures", "icd10.json")
    call_command("loaddata", path)
