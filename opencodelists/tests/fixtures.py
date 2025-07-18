"""This module contains fixtures to be used in all apps.

One of the design goals of the project is that there should be a limited and
controlled number of states that objects can be in.  This is achieved by
requiring (through convention) that the only way to alter the state of an
object is by calling a function in one of the actions.py modules. For more
information, see docs/adr/0004-business-logic-layer.md.

As such, test fixtures should only be created through invoking those actions.

However, this can make testing fiddly, since for instance to create a CodelistVersion in
a given state you might need to have an Organisation, a User, a Codelist, and other
CodelistVersions.  The approach we have taken is to build a "universe" of test objects
once, and then to pull out members of that universe as and when we need them.

Since each fixture function needs to do the same thing (find the member of the universe
with the given name, reload it from the database, and return it) we use build_fixture()
to avoid excessive duplication.

We use a very small subset of the SNOMED CT hierarchy.  For details, see
coding_systems/snomedct/fixtures/README.

There are fixtures for CodelistVersions with two different lists of codes:

    A) disorder-of-elbow
    B) disorder-of-elbow-excl-arthritis

The fixtures also create searches for "arthritis", "tennis", and "elbow".

The concepts returned by these searches are shown below, along with which of the two
lists of codes they belong to.


..  3723001    Arthritis
A.  439656005  └ Arthritis of elbow
A.  202855006    └ Lateral epicondylitis
..  116309007  Finding of elbow region
AB  128133004  ├ Disorder of elbow
AB  429554009  │ ├ Arthropathy of elbow
A.  439656005  │ │ └ Arthritis of elbow
A.  202855006  │ │   └ Lateral epicondylitis
AB  35185008   │ ├ Enthesopathy of elbow region
AB  73583000   │ │ └ Epicondylitis
A.  202855006  │ │   └ Lateral epicondylitis
AB  239964003  │ └ Soft tissue lesion of elbow region
..  298869002  └ Finding of elbow joint
AB  429554009    ├ Arthropathy of elbow
A.  439656005    │ └ Arthritis of elbow
A.  202855006    │   └ Lateral epicondylitis
..  298163003    └ Elbow joint inflamed
A.  439656005      └ Arthritis of elbow
A.  202855006        └ Lateral epicondylitis
..  238484001  Tennis toe
AB  156659008  (Epicondylitis &/or tennis elbow) or (golfers' elbow) [inactive]

And in a DAG (Tennis toe and (Epicondylitis &/or ...) not shown):

 ..──3723001─────┐              ..──116309007───┐
 │   Arthritis   │              │  Finding of   │
 │               │              │ elbow region  │
 └──────▲────────┘              └──────▲────────┘
        │                              │
        │            ..──298869002───┐ │ AB──128133004───┐
        │            │  Finding of   ├─┴─┤   Disorder    ◂────────────────────┐
        │            │  elbow joint  │   │   of elbow    │                    │
        │            └────────▲──────┘   └────────▲──────┘                    │
        │                     │                   │                           │
        │   ..──298163003───┐ │ AB──429554009───┐ │ AB──35185008────┐   AB──239964003──┐
        │   │  Elbow joint  ├─┴─┤  Arthropathy  ├─┴─┤ Enthesopathy  │   │ Soft tissue  │
        │   │   inflamed    │   │   of elbow    │   │of elbow region│   │  lesion of   │
        │   └──────▲────────┘   └──────▲────────┘   └──────▲────────┘   │ elbow region │
        │          │                   │                   │            └──────────────┘
        │          │ A.──439656005───┐ │            AB──73583000────┐
        └──────────┴─┤   Arthritis   ├─┘            │ Epicondylitis │
                     │   of elbow    │              │               │
                     └────────▲──────┘              └──────▲────────┘
                              │                            │
                              │ A.──202855006───┐          │
                              └─┤    Lateral    ├──────────┘
                                │ epicondylitis │
                                └───────────────┘

And here's a table of which codes are returned by searches for the terms "arthritis",
"tennis", and "elbow", and for the code "439656005":

                                                   arthritis  tennis  elbow  439656005
AB  156659008  (Epicondylitis &/or ...)                         X       X
..  3723001    Arthritis                               X
A.  439656005  Arthritis of elbow                      X                X       X
AB  429554009  Arthropathy of elbow                                     X
AB  128133004  Disorder of elbow                                        X
..  298163003  Elbow joint inflamed                                     X
AB  35185008   Enthesopathy of elbow region                             X
AB  73583000   Epicondylitis                                            X
..  298869002  Finding of elbow joint                                   X
..  116309007  Finding of elbow region                                  X
A.  202855006  Lateral epicondylitis                   X        X       X       X
AB  239964003  Soft tissue lesion of elbow region                       X
..  238484001  Tennis toe                                       X
"""

import csv
from copy import deepcopy
from io import StringIO
from pathlib import Path

import pytest
from django.conf import settings
from django.core.management import call_command
from django.db.models import Model

from builder.actions import create_search, save, update_code_statuses
from codelists.actions import (
    add_codelist_tag,
    add_collaborator,
    create_codelist_from_scratch,
    create_codelist_with_codes,
    create_old_style_codelist,
    create_old_style_version,
    export_to_builder,
)
from codelists.coding_systems import CODING_SYSTEMS, most_recent_database_alias
from codelists.models import Status
from codelists.search import do_search
from coding_systems.base.coding_system_base import BuilderCompatibleCodingSystem
from opencodelists.actions import (
    add_user_to_organisation,
    create_organisation,
    make_user_admin_for_organisation,
    set_api_token,
)
from opencodelists.models import User


SNOMED_FIXTURES_PATH = Path(settings.BASE_DIR, "coding_systems", "snomedct", "fixtures")
DMD_FIXTURES_PATH = Path(settings.BASE_DIR, "coding_systems", "dmd", "fixtures")
BNF_FIXTURES_PATH = Path(settings.BASE_DIR, "coding_systems", "bnf", "fixtures")
CODING_SYSTEM_RELEASES_FIXTURES_PATH = Path(
    settings.BASE_DIR, "coding_systems", "versioning", "fixtures"
)


def get_fixture_scope(fixture_name, config):
    if config.getoption("-m") == "functional":
        return "function"
    return "session"


def build_fixture(fixture_name):
    """Build a fixture function that returns the fixture object with the given name."""

    def fixture(universe):
        """The actual pytest fixture.

        Returns a copy of the member of the universe with the given name.
        """
        obj = universe[fixture_name]
        if isinstance(obj, Model):
            # Return instance of fixture loaded from the database.  We cannot use
            # obj.refresh_from_db(), because it does not work if the object has been
            # deleted in a test (because obj.pk is set to None when obj is deleted), and
            # because it does not reset any non-field attributes such as cached
            # properties.
            return type(obj).objects.get(pk=obj.pk)
        else:
            # Return a deep copy of the fixture.  This allows the fixture to be safely
            # mutated in tests.
            return deepcopy(obj)

    # This docstring is used in the output of `pytest --fixtures`
    fixture.__doc__ = f"Return {fixture_name} from the universe fixture"
    return pytest.fixture()(fixture)


@pytest.fixture(scope=get_fixture_scope)
def setup_coding_systems(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        # load the CodingSystemReleases needed for the snomed and dmd fixtures
        call_command(
            "loaddata",
            CODING_SYSTEM_RELEASES_FIXTURES_PATH / "coding_system_releases.json",
        )
    add_experimental_coding_system()


@pytest.fixture(scope=get_fixture_scope)
def snomedct_data(setup_coding_systems, django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        # load enough of the SNOMED CT hierarchy to be useful
        call_command(
            "loaddata",
            SNOMED_FIXTURES_PATH / "core-model-components.snomedct_test_20200101.json",
            database="snomedct_test_20200101",
        )
        call_command(
            "loaddata",
            SNOMED_FIXTURES_PATH / "tennis-elbow.snomedct_test_20200101.json",
            database="snomedct_test_20200101",
        )
        call_command(
            "loaddata",
            SNOMED_FIXTURES_PATH / "tennis-toe.snomedct_test_20200101.json",
            database="snomedct_test_20200101",
        )


@pytest.fixture(scope=get_fixture_scope)
def dmd_data(setup_coding_systems, django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        # load a very small amount of the DMD coding system
        call_command(
            "loaddata",
            DMD_FIXTURES_PATH / "asthma-medication.dmd_test_20200101.json",
            database="dmd_test_20200101",
        )


@pytest.fixture(scope=get_fixture_scope)
def bnf_data(setup_coding_systems, django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        # load a very small amount of the BNF coding system
        call_command(
            "loaddata",
            BNF_FIXTURES_PATH / "asthma.bnf_test_20200101.json",
            database="bnf_test_20200101",
        )


@pytest.fixture(scope=get_fixture_scope)
def dmd_bnf_mapping_data(setup_coding_systems, django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        # load a very small amount of the BNF coding system
        call_command(
            "loaddata",
            DMD_FIXTURES_PATH / "bnf_dmd_mapping.json",
            database="default",
        )


@pytest.fixture(scope=get_fixture_scope)
def universe(snomedct_data, dmd_data, bnf_data, django_db_setup, django_db_blocker):
    """Create universe of fixture objects.

    This fixture will be loaded exactly once per session.  It is not expected that it is
    used directly, but instead it is a dependency of the fixtures created by
    build_fixtures below.
    """
    with django_db_blocker.unblock():
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

    # enthesopathy_of_elbow_region_plus_tennis_toe
    enthesopathy_of_elbow_region_plus_tennis_toe = load_codes_from_csv(
        "enthesopathy-of-elbow-region-plus-tennis-toe.csv"
    )

    # asthma_medications_csv_data
    asthma_medication_csv_data = load_csv_data(
        "asthma-medication.csv", DMD_FIXTURES_PATH
    )

    # asthma_medication_csv_data_alternative_headers
    asthma_medication_csv_data_alternative_headers = load_csv_data(
        "asthma-medication-alt-headers.csv", DMD_FIXTURES_PATH
    )

    # asthma_medications_refill_csv_data
    asthma_medication_refill_csv_data = load_csv_data(
        "asthma-medication-refill.csv", DMD_FIXTURES_PATH
    )

    # asthma_medications_csv_data_no_header
    asthma_medication_csv_data_no_header = load_csv_data_no_header(
        "asthma-medication.csv", DMD_FIXTURES_PATH
    )

    # asthma_medications_refill_csv_data
    bnf_asthma_csv_data = load_codes_from_csv("asthma.csv", BNF_FIXTURES_PATH)

    # organisation
    # - has two users:
    #   - organisation_admin
    #   - organisation_user
    # - has three codelists:
    #   - old_style_codelist
    #   - new_style_codelist
    #   - codelist_from_scratch
    organisation = create_organisation(name="Test University", url="https://test.ac.uk")

    # another_organisation
    another_organisation = create_organisation(
        name="Another University", url="https://another.ac.uk"
    )

    # organisation_admin
    # - is admin for organisation
    organisation_admin = User.objects.create_user(
        username="alice", password="test", email="alice@test.ac.uk", name="Alice"
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
    organisation_user = User.objects.create_user(
        username="bob", password="test", email="bob@test.ac.uk", name="Bob"
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
    collaborator = User.objects.create_user(
        username="charlie",
        password="test",
        email="charlie@example.co.uk",
        name="Charlie",
    )

    # user_without_organisation
    # - does not belong to an organisation
    # - has no codelists
    user_without_organisation = User.objects.create_user(
        username="dave",
        password="test",
        email="dave@example.co.uk",
        name="Dave",
    )
    set_api_token(user=user_without_organisation)

    # user_with_no_api_token
    user_with_no_api_token = User.objects.create_user(
        username="eve",
        password="test",
        email="eve@example.co.uk",
        name="Eve",
    )

    # old_style_codelist
    # - owned by organisation
    # - has one version:
    #   - old_style_version
    # - tagged with "old-style"
    old_style_codelist = create_old_style_codelist(
        owner=organisation,
        name="Old-style Codelist",
        coding_system_id="snomedct",
        coding_system_database_alias=most_recent_database_alias("snomedct"),
        description="What this is",
        methodology="How we did it",
        csv_data=disorder_of_elbow_excl_arthritis_csv_data,
    )
    add_codelist_tag(codelist=old_style_codelist, tag="old-style")

    # old_style_version
    # - belongs to old_style_codelist
    # - includes Disorder of elbow
    old_style_version = create_old_style_version(
        codelist=old_style_codelist,
        csv_data=disorder_of_elbow_csv_data,
        coding_system_database_alias=most_recent_database_alias("snomedct"),
    )

    # Check that this version has the expected codes
    check_expected_codes(old_style_version, disorder_of_elbow_codes)

    # dmd codelist
    # - owned by organisation
    # - has 3 versions:
    #   - dmd_version_asthma_medication; contains CSV data with converted-from-BNF headers
    #   - dmd_version_asthma_medication_alt_headers; same data but headers "code" and "term"
    #   - dmd_version_asthma_medication_refill_csv_data; contains different data, including
    #     a code which is unknown in the current (test) coding system release
    dmd_codelist = create_old_style_codelist(
        owner=organisation,
        name="DMD Codelist",
        coding_system_id="dmd",
        coding_system_database_alias=most_recent_database_alias("dmd"),
        description="What this is",
        methodology="How we did it",
        csv_data=asthma_medication_csv_data,
    )
    dmd_version_asthma_medication = dmd_codelist.versions.first()
    dmd_version_asthma_medication_alt_headers = create_old_style_version(
        codelist=dmd_codelist,
        csv_data=asthma_medication_csv_data_alternative_headers,
        coding_system_database_alias=most_recent_database_alias("dmd"),
    )
    # In order to avoid raising and exception in the `create_old_style_version`
    # action because of the unknown code in the csv data, we create the
    # version with the csv_data set to asthma_medication_csv_data and
    # replace it with asthma_medication_refill_csv_data afterwards
    dmd_version_asthma_medication_refill = create_old_style_version(
        codelist=dmd_codelist,
        csv_data=asthma_medication_csv_data,
        coding_system_database_alias=most_recent_database_alias("dmd"),
    )
    dmd_version_asthma_medication_refill.csv_data = asthma_medication_refill_csv_data
    dmd_version_asthma_medication_refill.save()

    # In order to avoid raising and exception in the `create_old_style_version`
    # action because of the missing header in the csv data, we create the
    # version with the csv_data set to asthma_medication_csv_data and
    # replace it with asthma_medication_csv_data_no_header afterwards
    dmd_version_asthma_medication_no_header = create_old_style_version(
        codelist=dmd_codelist,
        csv_data=asthma_medication_csv_data,
        coding_system_database_alias=most_recent_database_alias("dmd"),
    )
    dmd_version_asthma_medication_no_header.csv_data = (
        asthma_medication_csv_data_no_header
    )
    dmd_version_asthma_medication_no_header.save()

    # bnf codelist
    # - owned by organisation
    # - has 1 versions:
    #   - bnf_version_asthma
    bnf_codelist = create_codelist_with_codes(
        owner=organisation,
        name="BNF Codelist",
        coding_system_id="bnf",
        coding_system_database_alias=most_recent_database_alias("bnf"),
        codes=bnf_asthma_csv_data,
        references=[
            {"text": "Reference 1", "url": "https://example.com/reference1"},
            {"text": "Reference 2", "url": "https://example.com/reference2"},
        ],
        signoffs=[
            {"user": organisation_user, "date": "2020-02-29"},
            {"user": collaborator, "date": "2020-02-29"},
        ],
        status=Status.PUBLISHED,
    )
    bnf_version_asthma = bnf_codelist.versions.first()

    # bnf_version_with_search
    # - belongs to bnf_codelist
    # - has a search, and all codes covered
    bnf_version_with_search = export_to_builder(
        version=bnf_version_asthma,
        author=organisation_user,
        coding_system_database_alias=most_recent_database_alias("bnf"),
    )
    create_search(
        draft=bnf_version_with_search,
        term="asthma",
        codes=codes_for_search_term("asthma", coding_system_id="bnf"),
    )
    update_code_statuses(
        draft=bnf_version_with_search,
        updates=[
            ("0301012A0AA", "+"),
            ("0301012A0AAABAB", "+"),
            ("0301012A0AAACAC", "+"),
        ],
    )

    # new_style_codelist
    # - belongs to organisation
    # - is collaborated on by collaborator
    # - has four versions:
    #   - version_with_no_searches
    #   - version_with_some_searches
    #   - version_with_complete_searches
    # - tagged with "new-style"
    new_style_codelist = create_codelist_with_codes(
        owner=organisation,
        name="New-style Codelist",
        coding_system_id="snomedct",
        coding_system_database_alias=most_recent_database_alias("snomedct"),
        codes=disorder_of_elbow_excl_arthritis_codes,
        references=[
            {"text": "Reference 1", "url": "https://example.com/reference1"},
            {"text": "Reference 2", "url": "https://example.com/reference2"},
        ],
        signoffs=[
            {"user": organisation_user, "date": "2020-02-29"},
            {"user": collaborator, "date": "2020-02-29"},
        ],
        status=Status.PUBLISHED,
    )
    add_codelist_tag(codelist=new_style_codelist, tag="new-style")

    # organisation_codelist
    # - an alias for new_style_codelist
    organisation_codelist = new_style_codelist

    # codelist
    # - an alias for new_style_codelist
    codelist = new_style_codelist

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

    # latest_published_version
    # - an alias for version_with_no_searches
    latest_published_version = version_with_no_searches
    assert latest_published_version.is_published

    # version_with_excluded_codes
    # - an alias for version_with_no_searches
    version_with_excluded_codes = version_with_no_searches

    # version_with_some_searches
    # - belongs to new_style_codelist
    # - has single search, but not all codes covered
    # - includes Disorder of elbow
    version_with_some_searches = export_to_builder(
        version=version_with_no_searches,
        author=organisation_user,
        coding_system_database_alias=most_recent_database_alias("snomedct"),
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
        version=version_with_some_searches,
        author=organisation_user,
        coding_system_database_alias=most_recent_database_alias("snomedct"),
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

    # version
    # - an alias for version_with_complete_searches
    version = version_with_complete_searches

    # version_under_review
    # - an alias for version_with_complete_searches
    version_under_review = version_with_complete_searches

    # latest_version
    # - an alias for version_with_complete_searches
    latest_version = version_with_complete_searches

    # codelist_with_collaborator
    # - an alias for new_style_codelist
    codelist_with_collaborator = new_style_codelist
    add_collaborator(codelist=codelist_with_collaborator, collaborator=collaborator)

    # codelist_from_scratch
    # - belongs to organisation
    # - has single version, being edited:
    #   - version_from_scratch
    # - tagged with "new-style"
    codelist_from_scratch = create_codelist_from_scratch(
        owner=organisation,
        name="Codelist From Scratch",
        coding_system_id="snomedct",
        coding_system_database_alias=most_recent_database_alias("snomedct"),
        author=organisation_user,
    )
    add_codelist_tag(codelist=codelist_from_scratch, tag="new-style")

    # user_codelist_from_scratch
    # - belongs to user
    # - has single version, being edited:
    #   - version_from_scratch
    # - tagged with "new-style"
    user_codelist_from_scratch = create_codelist_from_scratch(
        owner=organisation_user,
        name="User Codelist From Scratch",
        coding_system_id="snomedct",
        coding_system_database_alias=most_recent_database_alias("snomedct"),
        author=organisation_user,
    )
    add_codelist_tag(codelist=user_codelist_from_scratch, tag="new-style")

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
    # - tagged with "new-style"
    user_codelist = create_codelist_with_codes(
        owner=organisation_user,
        name="User-owned Codelist",
        coding_system_id="snomedct",
        coding_system_database_alias=most_recent_database_alias("snomedct"),
        codes=disorder_of_elbow_excl_arthritis_codes,
        status=Status.PUBLISHED,
    )
    add_codelist_tag(codelist=user_codelist, tag="new-style")

    # user_version
    # - belongs to user_codelist
    user_version = user_codelist.versions.get()

    # minimal codelist with codes
    # - belongs to organisation
    # - has 4 codes matching searches
    # - has one version
    #   - minimal_version_with_codes
    minimal_codelist = create_codelist_with_codes(
        owner=organisation,
        name="Minimal Codelist",
        coding_system_id="snomedct",
        coding_system_database_alias=most_recent_database_alias("snomedct"),
        codes=enthesopathy_of_elbow_region_plus_tennis_toe,
        status=Status.PUBLISHED,
    )
    # minimal_version
    # - belongs to minimal_codelist
    minimal_version = minimal_codelist.versions.get()
    minimal_draft = export_to_builder(
        version=minimal_version,
        author=organisation_user,
        coding_system_database_alias=most_recent_database_alias("snomedct"),
    )
    create_search(
        draft=minimal_draft,
        term="enthesopathy of elbow",
        codes=codes_for_search_term("enthesopathy of elbow"),
    )
    create_search(
        draft=minimal_draft,
        term="tennis toe",
        codes=codes_for_search_term("tennis toe"),
    )
    # Check that all code_objs are linked to searches
    assert not minimal_draft.code_objs.filter(results__isnull=True).exists()

    # null codelist
    # A codelist using the "null" coding system, which isn't associated with
    # a coding system database
    # Has 2 versions
    null_codelist = create_old_style_codelist(
        owner=organisation,
        name="Null Codelist",
        coding_system_id="null",
        coding_system_database_alias="null_test_20200101",
        csv_data="code,term\n1234,Test code",
        description="",
        methodology="",
    )
    null_version1 = null_codelist.versions.get()
    null_version2 = create_old_style_version(
        codelist=null_codelist,
        csv_data="code,term\n5678,Test code1",
        coding_system_database_alias="null_test_20200101",
    )

    add_experimental_coding_system()

    return locals()


def add_experimental_coding_system():
    # Add an experimental coding system i.e. one that is only visible behind a flag
    CODING_SYSTEMS["experiment"] = type(
        "ExperimentalCodingSystem",
        (BuilderCompatibleCodingSystem,),
        {
            "id": "experiment",
            "name": "Experimental Coding System",
            "short_name": "Beta",
            "description": "An experimental coding system available behind a flag",
            "is_experimental": True,
            "has_database": False,
        },
    )


def load_csv_data(filename, fixtures_path=None):
    """Return CSV data in given filename."""
    fixtures_path = fixtures_path or SNOMED_FIXTURES_PATH
    with open(fixtures_path / filename) as f:
        return f.read()


def load_csv_data_no_header(filename, fixtures_path=SNOMED_FIXTURES_PATH):
    """Return CSV data in given filename, dropping header."""
    with open(fixtures_path / filename) as f:
        rows = list(csv.reader(f))[1:]

    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerows(rows)
    return buffer.getvalue()


def load_codes_from_csv(filename, fixtures_path=None):
    """Return codes in CSV file at given filename."""
    fixtures_path = fixtures_path or SNOMED_FIXTURES_PATH
    with open(fixtures_path / filename) as f:
        rows = list(csv.reader(f))

    return [row[0] for row in rows[1:]]


def codes_for_search_term(term, coding_system_id=None):
    """Return codes matching search term."""
    coding_system_id = coding_system_id or "snomedct"
    coding_system = CODING_SYSTEMS[coding_system_id].get_by_release_or_most_recent()
    return do_search(coding_system, term=term)["all_codes"]


def codes_for_search_code(code):
    """Return codes matching search code."""

    coding_system = CODING_SYSTEMS["snomedct"].get_by_release_or_most_recent()
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
organisation = build_fixture("organisation")
another_organisation = build_fixture("another_organisation")
organisation_admin = build_fixture("organisation_admin")
organisation_user = build_fixture("organisation_user")
collaborator = build_fixture("collaborator")
user_without_organisation = build_fixture("user_without_organisation")
user = build_fixture("user")
user_with_no_api_token = build_fixture("user_with_no_api_token")
old_style_codelist = build_fixture("old_style_codelist")
old_style_version = build_fixture("old_style_version")
dmd_codelist = build_fixture("dmd_codelist")
dmd_version_asthma_medication = build_fixture("dmd_version_asthma_medication")
dmd_version_asthma_medication_alt_headers = build_fixture(
    "dmd_version_asthma_medication_alt_headers"
)
dmd_version_asthma_medication_refill = build_fixture(
    "dmd_version_asthma_medication_refill"
)
dmd_version_asthma_medication_no_headers = build_fixture(
    "dmd_version_asthma_medication_no_header"
)
bnf_version_asthma = build_fixture("bnf_version_asthma")
bnf_version_with_search = build_fixture("bnf_version_with_search")

new_style_codelist = build_fixture("new_style_codelist")
organisation_codelist = build_fixture("organisation_codelist")
codelist = build_fixture("codelist")
version_with_no_searches = build_fixture("version_with_no_searches")
version_with_some_searches = build_fixture("version_with_some_searches")
version_with_complete_searches = build_fixture("version_with_complete_searches")
version_with_excluded_codes = build_fixture("version_with_excluded_codes")
latest_published_version = build_fixture("latest_published_version")
latest_version = build_fixture("latest_version")
version = build_fixture("version")
version_under_review = build_fixture("version_under_review")
codelist_with_collaborator = build_fixture("codelist_with_collaborator")
codelist_from_scratch = build_fixture("codelist_from_scratch")
user_codelist_from_scratch = build_fixture("user_codelist_from_scratch")
version_from_scratch = build_fixture("version_from_scratch")
user_codelist = build_fixture("user_codelist")
user_version = build_fixture("user_version")
minimal_draft = build_fixture("minimal_draft")
null_codelist = build_fixture("null_codelist")


# These extra fixtures make modifications to those built in build_fixtures
@pytest.fixture
def draft_with_no_searches(version_with_no_searches, organisation_user):
    return export_to_builder(
        version=version_with_no_searches,
        author=organisation_user,
        coding_system_database_alias=most_recent_database_alias("snomedct"),
    )


@pytest.fixture
def draft_with_some_searches(version_with_some_searches, organisation_user):
    return export_to_builder(
        version=version_with_some_searches,
        author=organisation_user,
        coding_system_database_alias=most_recent_database_alias("snomedct"),
    )


@pytest.fixture
def draft_with_complete_searches(version_with_complete_searches, organisation_user):
    return export_to_builder(
        version=version_with_complete_searches,
        author=organisation_user,
        coding_system_database_alias=most_recent_database_alias("snomedct"),
    )


@pytest.fixture
def draft(draft_with_complete_searches):
    return draft_with_complete_searches


# This is a parameterized fixture.  When used in a test, the test will be run once for
# each of version_with_no_searches, version_with_some_searches,
# version_with_complete_searches.
@pytest.fixture(
    params=[
        "version_with_no_searches",
        "version_with_some_searches",
        "version_with_complete_searches",
    ],
)
def new_style_version(universe, request):
    version = universe[request.param]
    return type(version).objects.get(pk=version.pk)


@pytest.fixture(
    params=[
        "version_with_no_searches",
        "version_with_some_searches",
        "version_with_complete_searches",
    ],
)
def new_style_draft(universe, request, organisation_user):
    version = universe[request.param]
    return export_to_builder(
        version=version,
        author=organisation_user,
        coding_system_database_alias=most_recent_database_alias("snomedct"),
    )


@pytest.fixture
def create_codelists(organisation):
    """Fixture to create a batch of codelists with a specific status"""

    def _create_codelist(i, owner, status):
        new_codelist = create_codelist_from_scratch(
            owner=owner,
            name=f"Codelist {i}",
            coding_system_id="snomedct",
            coding_system_database_alias=most_recent_database_alias("snomedct"),
            author=None,
        )
        version = new_codelist.versions.last()
        version.status = status
        version.save()
        return new_codelist

    def make_codelist(number, owner=None, status=Status.PUBLISHED):
        return [
            _create_codelist(i, owner or organisation, status) for i in range(number)
        ]

    return make_codelist


@pytest.fixture
def icd10_data():
    path = Path(
        settings.BASE_DIR,
        "coding_systems",
        "icd10",
        "fixtures",
        "icd10.icd10_test_20200101.json",
    )
    call_command("loaddata", path, database="icd10_test_20200101")
