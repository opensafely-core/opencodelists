import re

import pytest

from codelists.coding_systems import CODING_SYSTEMS, most_recent_database_alias
from coding_systems.versioning.models import CodingSystemRelease, ReleaseState


@pytest.mark.parametrize("coding_system", list(CODING_SYSTEMS))
def test_most_recent_some_coding_system_releases(
    snomedct_data, dmd_data, icd10_data, coding_system
):
    # CodingSystemRelease created in fixtures for these
    if coding_system in ["ctv3", "dmd", "snomedct", "icd10", "bnf"]:
        assert (
            most_recent_database_alias(coding_system)
            == f"{coding_system}_test_20200101"
        )
    else:
        # no CodingSystemRelease created in fixtures for other coding systems
        with pytest.raises(
            CodingSystemRelease.DoesNotExist,
            match=re.escape(
                f"No coding system data found for {CODING_SYSTEMS[coding_system].short_name}"
            ),
        ):
            assert CODING_SYSTEMS[coding_system].get_by_release_or_most_recent()


def test_most_recent_multiple_coding_system_releases(
    snomedct_data, coding_system_release
):
    assert CodingSystemRelease.objects.filter(coding_system="snomedct").count() == 2
    assert most_recent_database_alias("snomedct") == "snomedct_v1_20221001"


@pytest.mark.parametrize(
    "database_alias,is_valid",
    [
        ("snomedct_v1_20221001", True),  # CSR set up with snomedct_data fixture
        ("snomedct_test_20200101", True),  # Matches the coding_system_release fixture
        ("snomedct_invalid_20200101", False),
    ],
)
def test_validate_db_alias(
    snomedct_data, coding_system_release, database_alias, is_valid
):
    # A db alias is only valid if there is an existing CodingSystemRelease that matches it
    if is_valid:
        CODING_SYSTEMS["snomedct"].validate_db_alias(database_alias) == database_alias
    else:
        with pytest.raises(
            AssertionError,
            match=f"{database_alias} is not a valid database alias for a SNOMED CT release.",
        ):
            CODING_SYSTEMS["snomedct"].validate_db_alias(database_alias)


@pytest.mark.parametrize(
    "database_alias,release_state,is_valid",
    [
        ("snomedct_v1_20221001", ReleaseState.READY, True),
        ("snomedct_v1_20221001", ReleaseState.IMPORTING, False),
        ("snomedct_test_20200101", ReleaseState.READY, True),
        ("snomedct_test_20200101", ReleaseState.IMPORTING, False),
    ],
)
def test_validate_db_alias_release_state(
    snomedct_data, coding_system_release, database_alias, release_state, is_valid
):
    # A db alias is only valid if its matching CodingSystemRelease is ready
    cs_release = CodingSystemRelease.objects.get(database_alias=database_alias)
    cs_release.state = release_state
    cs_release.save()
    if is_valid:
        CODING_SYSTEMS["snomedct"].validate_db_alias(database_alias) == database_alias
    else:
        with pytest.raises(
            AssertionError,
            match=f"{database_alias} is not a valid database alias for a SNOMED CT release.",
        ):
            CODING_SYSTEMS["snomedct"].validate_db_alias(database_alias)


@pytest.mark.parametrize(
    "database_alias,expected_version_name",
    [("snomedct_v1_20221001", "v1"), ("snomedct_test_20200101", "test"), (None, "v1")],
)
def test_get_by_release_or_most_recent(
    snomedct_data, coding_system_release, database_alias, expected_version_name
):
    assert (
        CODING_SYSTEMS["snomedct"]
        .get_by_release_or_most_recent(database_alias)
        .release_name
        == expected_version_name
    )


@pytest.mark.parametrize(
    "database_alias,expected_release_name",
    [
        ("snomedct_v1_20221001", "v1"),
        ("snomedct_test_20200101", "test"),
    ],
)
def test_release_name(
    snomedct_data, coding_system_release, database_alias, expected_release_name
):
    assert (
        CODING_SYSTEMS["snomedct"](database_alias).release_name == expected_release_name
    )
