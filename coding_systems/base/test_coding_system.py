import re

import pytest

from codelists.coding_systems import CODING_SYSTEMS
from coding_systems.versioning.models import CodingSystemVersion


@pytest.mark.parametrize("coding_system", list(CODING_SYSTEMS))
def test_most_recent_some_coding_system_versions(
    snomedct_data, dmd_data, icd10_data, coding_system
):
    # CodingSystemVersion created in fixtures for these
    if coding_system in ["ctv3", "dmd", "snomedct", "icd10"]:
        assert (
            CODING_SYSTEMS[coding_system].most_recent().version_slug
            == f"{coding_system}_test_20200101"
        )
    elif coding_system in ["opcs4", "null"]:
        assert CODING_SYSTEMS[coding_system].most_recent().version_slug == "none"
    else:
        # no CodingSystemVersion created in fixtures for readv2 or bnf
        with pytest.raises(
            CodingSystemVersion.DoesNotExist,
            match=re.escape(
                f"No coding system data found for {CODING_SYSTEMS[coding_system].short_name}"
            ),
        ):
            assert CODING_SYSTEMS[coding_system].most_recent()


def test_most_recent_multiple_coding_system_versions(
    snomedct_data, coding_system_version
):
    assert CodingSystemVersion.objects.filter(coding_system="snomedct").count() == 2
    assert (
        CODING_SYSTEMS["snomedct"].most_recent().version_slug == "snomedct_v1_20221001"
    )


@pytest.mark.parametrize(
    "slug,is_valid",
    [
        ("snomedct_v1_20221001", True),
        ("snomedct_test_20200101", True),
        ("snomedct_invalid_20200101", False),
    ],
)
def test_validate_db_alias(snomedct_data, coding_system_version, slug, is_valid):
    if is_valid:
        CODING_SYSTEMS["snomedct"].validate_db_alias(slug) == slug
    else:
        with pytest.raises(
            AssertionError,
            match=f"{slug} is not a valid database alias for a SNOMED CT version.",
        ):
            CODING_SYSTEMS["snomedct"].validate_db_alias(slug)


@pytest.mark.parametrize(
    "slug,expected_version_name",
    [("snomedct_v1_20221001", "v1"), ("snomedct_test_20200101", "test"), (None, "v1")],
)
def test_get_version_or_most_recent(
    snomedct_data, coding_system_version, slug, expected_version_name
):
    assert (
        CODING_SYSTEMS["snomedct"].get_version_or_most_recent(slug).version_name
        == expected_version_name
    )


@pytest.mark.parametrize(
    "db_alias,expected_version_name",
    [
        ("snomedct_v1_20221001", "v1"),
        ("snomedct_test_20200101", "test"),
    ],
)
def test_version_name(
    snomedct_data, coding_system_version, db_alias, expected_version_name
):
    assert CODING_SYSTEMS["snomedct"](db_alias).version_name == expected_version_name
