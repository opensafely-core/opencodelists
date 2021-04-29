import pytest
from django.db.utils import IntegrityError

from codelists.actions import export_to_builder
from codelists.models import CodelistVersion, Handle
from opencodelists.tests.factories import OrganisationFactory, UserFactory


def test_handle_cannot_belong_to_user_and_organisation():
    with pytest.raises(IntegrityError):
        Handle.objects.create(
            name="Test",
            user=UserFactory(),
            organisation=OrganisationFactory(),
        )


def test_handle_must_belong_to_user_or_organisation():
    with pytest.raises(IntegrityError):
        Handle.objects.create(
            name="Test",
        )


def test_old_style_codes(old_style_version):
    assert old_style_version.codes == (
        "128133004",
        "156659008",
        "202855006",
        "239964003",
        "35185008",
        "429554009",
        "439656005",
        "73583000",
    )


def test_old_style_table(old_style_version):
    assert old_style_version.table == [
        ["id", "name"],
        ["429554009", "Arthropathy of elbow (disorder)"],
        ["128133004", "Disorder of elbow (disorder)"],
        ["202855006", "Lateral epicondylitis (disorder)"],
        ["439656005", "Arthritis of elbow (disorder)"],
        ["73583000", "Epicondylitis (disorder)"],
        ["35185008", "Enthesopathy of elbow region (disorder)"],
        ["239964003", "Soft tissue lesion of elbow region (disorder)"],
        [
            "156659008",
            "(Epicondylitis &/or tennis elbow) or (golfers' elbow) (disorder)",
        ],
    ]


def test_old_style_codeset(old_style_version):
    assert old_style_version.codeset.codes() == set(old_style_version.codes)


def test_new_style_codes(version_with_some_searches):
    assert version_with_some_searches.codes == (
        "128133004",
        "156659008",
        "202855006",
        "239964003",
        "35185008",
        "429554009",
        "439656005",
        "73583000",
    )


def test_new_style_table(version_with_some_searches):
    assert version_with_some_searches.table == [
        ["code", "term"],
        ["128133004", "Disorder of elbow"],
        ["156659008", "(Epicondylitis &/or tennis elbow) or (golfers' elbow)"],
        ["202855006", "Lateral epicondylitis"],
        ["239964003", "Soft tissue lesion of elbow region"],
        ["35185008", "Enthesopathy of elbow region"],
        ["429554009", "Arthropathy of elbow"],
        ["439656005", "Arthritis of elbow"],
        ["73583000", "Epicondylitis"],
    ]


def test_new_style_codeset(version_with_some_searches):
    assert version_with_some_searches.codeset.codes() == set(
        version_with_some_searches.codes
    )


def test_old_style_is_new_style(old_style_codelist):
    assert not old_style_codelist.is_new_style()


def test_new_style_is_new_style(new_style_codelist):
    assert new_style_codelist.is_new_style()


def test_latest_version(
    new_style_codelist, version_with_complete_searches, organisation_user
):
    # Check that the latest version is the last created version
    assert new_style_codelist.latest_version() == version_with_complete_searches

    # Create a new draft version
    export_to_builder(version=version_with_complete_searches, owner=organisation_user)

    # Check that the latest version is unchanged
    assert new_style_codelist.latest_version() == version_with_complete_searches


def test_latest_version_for_new_codelist(codelist_from_scratch, organisation_user):
    assert codelist_from_scratch.latest_version() is None


def test_get_by_hash(new_style_version):
    assert (
        CodelistVersion.objects.get_by_hash(new_style_version.hash) == new_style_version
    )
