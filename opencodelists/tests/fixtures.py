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
from io import StringIO
from pathlib import Path

import pytest
from django.conf import settings
from django.core.management import call_command

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


#################################################################################
# Load coding system data
#################################################################################


@pytest.fixture(scope=get_fixture_scope)
def setup_coding_systems(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        # load the CodingSystemReleases needed for the snomed and dmd fixtures
        call_command(
            "loaddata",
            CODING_SYSTEM_RELEASES_FIXTURES_PATH / "coding_system_releases.json",
        )


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
def dmd_bnf_mapping_data(
    setup_coding_systems, dmd_data, bnf_data, django_db_setup, django_db_blocker
):
    with django_db_blocker.unblock():
        # load a very small amount of the BNF coding system
        call_command(
            "loaddata",
            DMD_FIXTURES_PATH / "bnf_dmd_mapping.json",
            database="default",
        )


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


#################################################################################
# Load CSV Data
#################################################################################


def load_csv_data(filename, fixtures_path=None):
    """Return CSV data in given filename."""
    fixtures_path = fixtures_path or SNOMED_FIXTURES_PATH
    with open(fixtures_path / filename) as f:
        return f.read()


def load_csv_data_no_header(filename):
    """Return CSV data in given filename, dropping header."""
    with open(SNOMED_FIXTURES_PATH / filename) as f:
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


# These just sit in memory, per-session is fine
# Maybe we should make them an immutable data structure for safety


@pytest.fixture(scope="session")
def disorder_of_elbow_codes():
    return load_codes_from_csv("disorder-of-elbow.csv")


@pytest.fixture(scope="session")
def disorder_of_elbow_excl_arthritis_codes():
    return load_codes_from_csv("disorder-of-elbow-excl-arthritis.csv")


@pytest.fixture(scope="session")
def disorder_of_elbow_csv_data():
    return load_csv_data("disorder-of-elbow.csv")


@pytest.fixture(scope="session")
def disorder_of_elbow_excl_arthritis_csv_data():
    return load_csv_data("disorder-of-elbow-excl-arthritis.csv")


@pytest.fixture(scope="session")
def disorder_of_elbow_csv_data_no_header():
    return load_csv_data_no_header("disorder-of-elbow.csv")


@pytest.fixture(scope="session")
def enthesopathy_of_elbow_region_plus_tennis_toe():
    return load_codes_from_csv("enthesopathy-of-elbow-region-plus-tennis-toe.csv")


@pytest.fixture(scope="session")
def asthma_medication_csv_data():
    return load_csv_data("asthma-medication.csv", DMD_FIXTURES_PATH)


@pytest.fixture(scope="session")
def asthma_medication_csv_data_alternative_headers():
    return load_csv_data("asthma-medication-alt-headers.csv", DMD_FIXTURES_PATH)


@pytest.fixture(scope="session")
def asthma_medication_refill_csv_data():
    return load_csv_data("asthma-medication-refill.csv", DMD_FIXTURES_PATH)


@pytest.fixture(scope="session")
def bnf_asthma_csv_data():
    return load_codes_from_csv("asthma.csv", BNF_FIXTURES_PATH)


#################################################################################
# Orgs and users
#################################################################################


# organisation
# - has two users:
#   - organisation_admin
#   - organisation_user
# - has three codelists:
#   - old_style_codelist
#   - new_style_codelist
#   - codelist_from_scratch


@pytest.fixture
def organisation():
    return create_organisation(name="Test University", url="https://test.ac.uk")


@pytest.fixture
def another_organisation():
    return create_organisation(name="Another University", url="https://another.ac.uk")


@pytest.fixture
def organisation_admin(organisation):
    organisation_admin = User.objects.create_user(
        username="alice", password="test", email="alice@test.ac.uk", name="Alice"
    )
    add_user_to_organisation(
        user=organisation_admin, organisation=organisation, date_joined="2020-02-29"
    )
    make_user_admin_for_organisation(user=organisation_admin, organisation=organisation)
    return organisation_admin


@pytest.fixture
def organisation_user(organisation):
    organisation_user = User.objects.create_user(
        username="bob", password="test", email="bob@test.ac.uk", name="Bob"
    )
    add_user_to_organisation(
        user=organisation_user, organisation=organisation, date_joined="2020-02-29"
    )
    set_api_token(user=organisation_user)
    return organisation_user


# collaborator
# - is collaborator on new_style_codelist
@pytest.fixture
def collaborator():
    return User.objects.create_user(
        username="charlie",
        password="test",
        email="charlie@example.co.uk",
        name="Charlie",
    )


@pytest.fixture
def user(organisation_user):
    return organisation_user


@pytest.fixture
def user_without_organisation():
    user_without_organisation = User.objects.create_user(
        username="dave",
        password="test",
        email="dave@example.co.uk",
        name="Dave",
    )
    set_api_token(user=user_without_organisation)
    return user_without_organisation


@pytest.fixture
def user_with_no_api_token():
    user_with_no_api_token = User.objects.create_user(
        username="eve",
        password="test",
        email="eve@example.co.uk",
        name="Eve",
    )
    return user_with_no_api_token


#################################################################################
# Codelists and versions - SNOMEDCT coding system
#################################################################################


def check_expected_codes(version, codes):
    assert sorted(version.codes) == sorted(codes)


# old_style_codelist
# - owned by organisation
# - has one version:
#   - old_style_version
# - tagged with "old-style"
@pytest.fixture
def old_style_codelist(
    snomedct_data, organisation, disorder_of_elbow_excl_arthritis_csv_data
):
    codelist = create_old_style_codelist(
        owner=organisation,
        name="Old-style Codelist",
        coding_system_id="snomedct",
        coding_system_database_alias=most_recent_database_alias("snomedct"),
        description="What this is",
        methodology="How we did it",
        csv_data=disorder_of_elbow_excl_arthritis_csv_data,
    )
    add_codelist_tag(codelist=codelist, tag="old-style")
    return codelist


# old_style_version
# - belongs to old_style_codelist
# - includes Disorder of elbow
@pytest.fixture
def old_style_version(
    old_style_codelist, disorder_of_elbow_csv_data, disorder_of_elbow_codes
):
    version = create_old_style_version(
        codelist=old_style_codelist,
        csv_data=disorder_of_elbow_csv_data,
        coding_system_database_alias=most_recent_database_alias("snomedct"),
    )
    check_expected_codes(version, disorder_of_elbow_codes)
    return version


# new_style_codelist
# - belongs to organisation
# - is collaborated on by collaborator
# - has four versions:
#   - version_with_no_searches
#   - version_with_some_searches
#   - version_with_complete_searches
# - tagged with "new-style"
@pytest.fixture
def new_style_codelist(
    snomedct_data,
    organisation,
    organisation_user,
    collaborator,
    disorder_of_elbow_excl_arthritis_codes,
):
    codelist = create_codelist_with_codes(
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
    add_collaborator(codelist=codelist, collaborator=collaborator)
    add_codelist_tag(codelist=codelist, tag="new-style")
    return codelist


# organisation_codelist
# - an alias for new_style_codelist
@pytest.fixture
def organisation_codelist(new_style_codelist):
    return new_style_codelist


# codelist
# - an alias for new_style_codelist
@pytest.fixture
def codelist(new_style_codelist):
    return new_style_codelist


# codelist_with_collaborator
# - an alias for new_style_codelist
@pytest.fixture
def codelist_with_collaborator(new_style_codelist):
    return new_style_codelist


# version_with_no_searches
# - belongs to new_style_codelist
# - has no searches
# - includes Disorder of elbow, excludes Arthritis
@pytest.fixture
def version_with_no_searches(
    new_style_codelist, disorder_of_elbow_excl_arthritis_codes
):
    version = new_style_codelist.versions.get()
    # Check that no code_objs are linked to searches
    assert not version.code_objs.filter(results__isnull=False).exists()

    # Check that this version has the expected codes
    check_expected_codes(version, disorder_of_elbow_excl_arthritis_codes)
    return version


# latest_published_version
# - an alias for version_with_no_searches
@pytest.fixture
def latest_published_version(version_with_no_searches):
    assert version_with_no_searches.is_published
    return version_with_no_searches


# version_with_excluded_codes
# - an alias for version_with_no_searches
@pytest.fixture
def version_with_excluded_codes(version_with_no_searches):
    return version_with_no_searches


# version_with_some_searches
# - belongs to new_style_codelist
# - has single search, but not all codes covered
# - includes Disorder of elbow
@pytest.fixture
def version_with_some_searches(
    version_with_no_searches, organisation_user, disorder_of_elbow_codes
):
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

    return version_with_some_searches


# version_with_complete_searches
# - belongs to new_style_codelist
# - has some searches, and all codes covered
# - includes Disorder of elbow
@pytest.fixture
def version_with_complete_searches(
    version_with_some_searches, organisation_user, disorder_of_elbow_codes
):
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

    return version_with_complete_searches


# version
# - an alias for version_with_complete_searches
@pytest.fixture
def version(version_with_complete_searches):
    return version_with_complete_searches


# version_under_review
# - an alias for version_with_complete_searches
@pytest.fixture
def version_under_review(version_with_complete_searches):
    return version_with_complete_searches


# latest_version
# - an alias for version_with_complete_searches
@pytest.fixture
def latest_version(version_with_complete_searches):
    return version_with_complete_searches


# codelist_from_scratch
# - belongs to organisation
# - has single version, being edited:
#   - version_from_scratch
# - tagged with "new-style"
@pytest.fixture
def codelist_from_scratch(snomedct_data, organisation, organisation_user):
    codelist_from_scratch = create_codelist_from_scratch(
        owner=organisation,
        name="Codelist From Scratch",
        coding_system_id="snomedct",
        coding_system_database_alias=most_recent_database_alias("snomedct"),
        author=organisation_user,
    )
    add_codelist_tag(codelist=codelist_from_scratch, tag="new-style")
    return codelist_from_scratch


# user_codelist_from_scratch
# - belongs to user
# - has single version, being edited:
#   - version_from_scratch
# - tagged with "new-style"
@pytest.fixture
def user_codelist_from_scratch(snomedct_data, organisation_user):
    user_codelist_from_scratch = create_codelist_from_scratch(
        owner=organisation_user,
        name="User Codelist From Scratch",
        coding_system_id="snomedct",
        coding_system_database_alias=most_recent_database_alias("snomedct"),
        author=organisation_user,
    )
    add_codelist_tag(codelist=user_codelist_from_scratch, tag="new-style")
    return user_codelist_from_scratch


# version_from_scratch
# - belongs to codelist_from_scratch
# - being edited by organisation_user
@pytest.fixture
def version_from_scratch(codelist_from_scratch):
    version_from_scratch = codelist_from_scratch.versions.get()
    assert version_from_scratch.codes == ()
    return version_from_scratch


# user_codelist
# - belongs to organisation_user
# - has one version:
#   - user_version
# - tagged with "new-style"
@pytest.fixture
def user_codelist(
    snomedct_data, organisation_user, disorder_of_elbow_excl_arthritis_codes
):
    user_codelist = create_codelist_with_codes(
        owner=organisation_user,
        name="User-owned Codelist",
        coding_system_id="snomedct",
        coding_system_database_alias=most_recent_database_alias("snomedct"),
        codes=disorder_of_elbow_excl_arthritis_codes,
        status=Status.PUBLISHED,
    )
    add_codelist_tag(codelist=user_codelist, tag="new-style")
    return user_codelist


# user_version
# - belongs to user_codelist
@pytest.fixture
def user_version(user_codelist):
    return user_codelist.versions.get()


# minimal codelist with codes
# - belongs to organisation
# - has 4 codes matching searches
# - has one version
#   - minimal_version_with_codes
@pytest.fixture
def minimal_codelist(
    snomedct_data, organisation, enthesopathy_of_elbow_region_plus_tennis_toe
):
    return create_codelist_with_codes(
        owner=organisation,
        name="Minimal Codelist",
        coding_system_id="snomedct",
        coding_system_database_alias=most_recent_database_alias("snomedct"),
        codes=enthesopathy_of_elbow_region_plus_tennis_toe,
        status=Status.PUBLISHED,
    )


# minimal_version
# - belongs to minimal_codelist
@pytest.fixture
def minimal_draft(minimal_codelist, organisation_user):
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
    return minimal_draft


#################################################################################
# Codelists and versions - Null coding system
#################################################################################


# null codelist
# A codelist using the "null" coding system, which isn't associated with
# a coding system database
# Has 2 versions
@pytest.fixture
def null_codelist(organisation):
    null_codelist = create_old_style_codelist(
        owner=organisation,
        name="Null Codelist",
        coding_system_id="null",
        coding_system_database_alias="null_test_20200101",
        csv_data="code,term\n1234,Test code",
        description="",
        methodology="",
    )
    null_codelist.versions.get()
    create_old_style_version(
        codelist=null_codelist,
        csv_data="code,term\n5678,Test code1",
        coding_system_database_alias="null_test_20200101",
    )
    return null_codelist


#################################################################################
# Codelists and versions - DMD coding system
#################################################################################


# dmd codelist
# - owned by organisation
# - has 3 versions:
#   - dmd_version_asthma_medication; contains CSV data with converted-from-BNF headers
#   - dmd_version_asthma_medication_alt_headers; same data but headers "code" and "term"
#   - dmd_version_asthma_medication_refill_csv_data; contains different data, including
#     a code which is unknown in the current (test) coding system release
@pytest.fixture
def dmd_codelist(dmd_data, organisation, asthma_medication_csv_data):
    return create_old_style_codelist(
        owner=organisation,
        name="DMD Codelist",
        coding_system_id="dmd",
        coding_system_database_alias=most_recent_database_alias("dmd"),
        description="What this is",
        methodology="How we did it",
        csv_data=asthma_medication_csv_data,
    )


@pytest.fixture
def dmd_version_asthma_medication(dmd_codelist):
    return dmd_codelist.versions.first()


@pytest.fixture
def dmd_version_asthma_medication_alt_headers(
    dmd_codelist, asthma_medication_csv_data_alternative_headers
):
    return create_old_style_version(
        codelist=dmd_codelist,
        csv_data=asthma_medication_csv_data_alternative_headers,
        coding_system_database_alias=most_recent_database_alias("dmd"),
    )


@pytest.fixture
def dmd_version_asthma_medication_refill(
    dmd_codelist, asthma_medication_csv_data, asthma_medication_refill_csv_data
):
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
    return dmd_version_asthma_medication_refill


#################################################################################
# Codelists and versions - BNF coding system
#################################################################################
# bnf codelist
# - owned by organisation
# - has 1 versions:
#   - bnf_version_asthma
@pytest.fixture
def bnf_codelist(
    bnf_data, organisation, organisation_user, collaborator, bnf_asthma_csv_data
):
    return create_codelist_with_codes(
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


@pytest.fixture
def bnf_version_asthma(bnf_codelist):
    return bnf_codelist.versions.first()


# bnf_version_with_search
# - belongs to bnf_codelist
# - has a search, and all codes covered
@pytest.fixture
def bnf_version_with_search(organisation_user, bnf_version_asthma):
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
    return bnf_version_with_search


#################################################################################
# Fixtures combining many of the above codelists
#################################################################################


@pytest.fixture
def many_organisation_codelists(
    bnf_codelist,
    codelist_from_scratch,
    dmd_codelist,
    minimal_codelist,
    new_style_codelist,
    null_codelist,
    old_style_codelist,
):
    pass


@pytest.fixture
def many_organisation_versions(
    bnf_version_asthma,
    bnf_version_with_search,
    version_from_scratch,
    dmd_version_asthma_medication,
    dmd_version_asthma_medication_alt_headers,
    dmd_version_asthma_medication_refill,
    minimal_draft,
    version_with_no_searches,
    version_with_some_searches,
    version_with_complete_searches,
    null_codelist,
    old_style_version,
):
    pass


@pytest.fixture
def many_organisation_and_user_codelists(
    many_organisation_codelists, user_codelist, user_codelist_from_scratch
):
    pass


@pytest.fixture
def all_fixtures(
    many_organisation_and_user_codelists,
    many_organisation_versions,
    another_organisation,
    organisation_admin,
    collaborator,
    user_without_organisation,
    user_with_no_api_token,
    user_version,
    codelist_with_collaborator,
):
    pass


#################################################################################
# misc
#################################################################################


def codes_for_search_term(term, coding_system_id=None):
    """Return codes matching search term."""
    coding_system_id = coding_system_id or "snomedct"
    coding_system = CODING_SYSTEMS[coding_system_id].get_by_release_or_most_recent()
    return do_search(coding_system, term=term)["all_codes"]


def codes_for_search_code(code):
    """Return codes matching search code."""

    coding_system = CODING_SYSTEMS["snomedct"].get_by_release_or_most_recent()
    return do_search(coding_system, code=code)["all_codes"]


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
def new_style_version(
    request,
    version_with_no_searches,
    version_with_some_searches,
    version_with_complete_searches,
):
    available_versions = {
        "version_with_no_searches": version_with_no_searches,
        "version_with_some_searches": version_with_some_searches,
        "version_with_complete_searches": version_with_complete_searches,
    }
    version = available_versions[request.param]
    return type(version).objects.get(pk=version.pk)


@pytest.fixture(
    params=[
        "version_with_no_searches",
        "version_with_some_searches",
        "version_with_complete_searches",
    ],
)
def new_style_draft(
    organisation_user,
    request,
    version_with_no_searches,
    version_with_some_searches,
    version_with_complete_searches,
):
    available_versions = {
        "version_with_no_searches": version_with_no_searches,
        "version_with_some_searches": version_with_some_searches,
        "version_with_complete_searches": version_with_complete_searches,
    }

    version = available_versions[request.param]
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
