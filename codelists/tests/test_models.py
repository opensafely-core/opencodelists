import pytest
from django.db.utils import IntegrityError

from codelists.models import Codelist, CodelistVersion
from opencodelists.tests.factories import OrganisationFactory, UserFactory


def test_codelist_cannot_belong_to_user_and_organisation():
    with pytest.raises(IntegrityError):
        Codelist.objects.create(
            name="Test",
            coding_system_id="snomedct",
            description="blah",
            methodology="blah",
            user=UserFactory(),
            organisation=OrganisationFactory(),
        )


def test_codelist_must_belong_to_user_or_organisation():
    with pytest.raises(IntegrityError):
        Codelist.objects.create(
            name="Test",
            coding_system_id="snomedct",
            description="blah",
            methodology="blah",
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


def test_old_style_is_new_style(old_style_codelist):
    assert not old_style_codelist.is_new_style()


def test_new_style_is_new_style(new_style_codelist):
    assert new_style_codelist.is_new_style()


def test_get_by_hash(new_style_version):
    assert (
        CodelistVersion.objects.get_by_hash(new_style_version.hash) == new_style_version
    )
