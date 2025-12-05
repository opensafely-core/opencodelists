import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from builder import actions as builder_actions
from codelists.models import CodelistVersion, DeleteHandleException, Handle


def test_handle_cannot_belong_to_user_and_organisation(codelist, user, organisation):
    with pytest.raises(IntegrityError, match="codelists_handle_organisation_xor_user"):
        Handle.objects.create(
            codelist=codelist,
            name="Test",
            slug="test",
            is_current=True,
            user=user,
            organisation=organisation,
        )


def test_handle_must_belong_to_user_or_organisation(codelist):
    with pytest.raises(IntegrityError, match="codelists_handle_organisation_xor_user"):
        Handle.objects.create(
            codelist=codelist,
            name="Test",
            slug="test",
            is_current=True,
        )


def test_handle_slug_and_name_can_be_reused_by_different_organisation(
    codelist, another_organisation
):
    Handle.objects.create(
        codelist=codelist,
        name=codelist.name,
        slug=codelist.slug,
        is_current=True,
        organisation=another_organisation,
    )


def test_handle_slug_and_name_can_be_reused_by_different_user(codelist, user):
    Handle.objects.create(
        codelist=codelist,
        name=codelist.name,
        slug=codelist.slug,
        is_current=True,
        user=user,
    )


def test_handle_slug_cannot_be_reused_by_organisation(codelist):
    with pytest.raises(
        IntegrityError,
        match="UNIQUE constraint failed: codelists_handle.organisation_id, codelists_handle.slug",
    ):
        Handle.objects.create(
            codelist=codelist,
            name="New name",
            slug=codelist.slug,
            is_current=True,
            organisation=codelist.organisation,
        )


def test_handle_name_cannot_be_reused_by_organisation(codelist):
    with pytest.raises(
        IntegrityError,
        match="UNIQUE constraint failed: codelists_handle.organisation_id, codelists_handle.name",
    ):
        Handle.objects.create(
            codelist=codelist,
            name=codelist.name,
            slug="new-slug",
            is_current=True,
            organisation=codelist.organisation,
        )


def test_handle_slug_cannot_be_reused_by_user(user_codelist):
    with pytest.raises(
        IntegrityError,
        match="UNIQUE constraint failed: codelists_handle.user_id, codelists_handle.slug",
    ):
        Handle.objects.create(
            codelist=user_codelist,
            name="New name",
            slug=user_codelist.slug,
            is_current=True,
            user=user_codelist.user,
        )


def test_handle_name_cannot_be_reused_by_user(user_codelist):
    with pytest.raises(
        IntegrityError,
        match="UNIQUE constraint failed: codelists_handle.user_id, codelists_handle.name",
    ):
        Handle.objects.create(
            codelist=user_codelist,
            name=user_codelist.name,
            slug="new-slug",
            is_current=True,
            user=user_codelist.user,
        )


def test_handle_name_only_alphanumeric_hyphen_underscore(codelist):
    with pytest.raises(
        ValidationError,
        match="Codelist names must contain at least one letter or number.",
    ):
        handle = Handle.objects.create(
            codelist=codelist,
            name="!",
            slug="new-slug",
            is_current=True,
            organisation=codelist.organisation,
        )
        handle._meta.get_field("name").clean(handle.name, handle)


def test_handle_name_non_blank(codelist):
    with pytest.raises(
        ValidationError,
        match="This field cannot be blank.",
    ):
        handle = Handle.objects.create(
            codelist=codelist,
            name="",
            slug="new-slug",
            is_current=True,
            organisation=codelist.organisation,
        )
        handle._meta.get_field("name").clean(handle.name, handle)


def test_handle_name_validation_valid(user_codelist):
    name = "new-codelist_validname123!,\"'."
    handle = Handle.objects.create(
        codelist=user_codelist,
        name=name,
        slug="new-slug",
        is_current=True,
        user=user_codelist.user,
    )
    clean_name = handle._meta.get_field("name").clean(handle.name, handle)

    assert clean_name == name


def test_handle_delete_not_allowed_method(codelist):
    with pytest.raises(DeleteHandleException):
        codelist.current_handle.delete()


def test_handle_delete_not_allowed_queryset(codelist):
    with pytest.raises(DeleteHandleException):
        Handle.objects.first().delete()


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


def test_old_style_codes_no_header(dmd_version_asthma_medication_no_headers):
    assert dmd_version_asthma_medication_no_headers.codes == (
        "10514511000001106",
        "10525011000001107",
    )


def test_old_style_table(old_style_version):
    assert old_style_version.table == [
        ["code", "name"],
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


def test_old_style_formatted_table_with_fixed_headers(old_style_version):
    assert old_style_version.formatted_table(fixed_headers=True) == [
        ["code", "term"],
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


def test_visible_versions_user_has_edit_permissions(
    new_style_codelist,
    user,
):
    assert len(new_style_codelist.visible_versions(user)) == 3


def test_visible_versions_user_doesnt_have_edit_permissions(
    new_style_codelist,
    user_without_organisation,
):
    assert len(new_style_codelist.visible_versions(user_without_organisation)) == 1


def test_visible_versions_can_include_requested_version(
    new_style_codelist,
    latest_published_version,
    version_under_review,
    user_without_organisation,
):
    visible_without_included = list(
        new_style_codelist.visible_versions(user_without_organisation)
    )
    assert visible_without_included == [latest_published_version]

    visible_with_included = list(
        new_style_codelist.visible_versions(
            user=user_without_organisation, include_version_id=version_under_review.id
        )
    )
    assert latest_published_version in visible_with_included
    assert version_under_review in visible_with_included
    assert len(visible_with_included) == 2


def test_latest_visible_version_user_has_edit_permissions(
    new_style_codelist,
    latest_version,
    user,
):
    assert new_style_codelist.latest_visible_version(user) == latest_version


def test_latest_visible_version_user_doesnt_have_edit_permissions(
    new_style_codelist,
    latest_published_version,
    user_without_organisation,
):
    assert (
        new_style_codelist.latest_visible_version(user_without_organisation)
        == latest_published_version
    )


def test_latest_visible_version_no_versions_visible(
    codelist_from_scratch, user_without_organisation
):
    assert (
        codelist_from_scratch.latest_visible_version(user_without_organisation) is None
    )


def test_get_by_hash(new_style_version):
    assert (
        CodelistVersion.objects.get_by_hash(new_style_version.hash) == new_style_version
    )


def test_codelist_has_published_versions_returns_true_when_published(
    new_style_codelist,
):
    assert new_style_codelist.has_published_versions()


def test_codelist_has_published_versions_returns_false_when_not_published(
    old_style_codelist,
):
    assert not old_style_codelist.has_published_versions()


def test_latest_published_version_no_versions_published(codelist_from_scratch):
    assert codelist_from_scratch.latest_published_version() is None


def test_latest_published_version_with_version_published(
    new_style_codelist, latest_published_version
):
    assert new_style_codelist.latest_published_version() == latest_published_version


def test_get_latest_published_url(new_style_codelist, latest_published_version):
    assert (
        new_style_codelist.get_latest_published_url()
        == latest_published_version.get_absolute_url()
    )


def test_get_latest_published_url_no_published_version(codelist_from_scratch):
    assert (
        codelist_from_scratch.get_latest_published_url()
        == codelist_from_scratch.get_absolute_url()
    )


@pytest.mark.parametrize(
    "new_code_header,is_downloadable",
    [
        ("snomedcode", True),
        ("SnomedCode", True),
        ("bnf_code", False),
    ],
)
def test_downloadable(old_style_version, new_code_header, is_downloadable):
    assert old_style_version.downloadable
    assert old_style_version.table[0] == ["code", "name"]

    # change code header
    old_style_version.csv_data = old_style_version.csv_data.replace(
        "code,name", f"{new_code_header},name"
    )
    old_style_version.save()

    assert old_style_version.downloadable == is_downloadable


def test_draft_is_not_downloadable(draft_with_no_searches):
    assert draft_with_no_searches.downloadable is False
    builder_actions.save(draft=draft_with_no_searches)
    assert draft_with_no_searches.downloadable is True


def test_cached_csv_data(old_style_version):
    assert old_style_version.cached_csv_data == {}
    old_style_version.csv_data_shas()
    assert old_style_version.cached_csv_data["release"] == "snomedct_test_20200101"
    assert (
        "download_data_fixed_headers_False_include_mapped_vmps_True"
        in old_style_version.cached_csv_data
    )
    assert (
        old_style_version.cached_csv_data[
            "download_data_fixed_headers_False_include_mapped_vmps_True"
        ]
        == old_style_version.csv_data
    )
    assert len(old_style_version.cached_csv_data["shas"]) == 1


def test_cached_csv_data_dmd_codelist(dmd_version_asthma_medication):
    clv = dmd_version_asthma_medication
    assert clv.cached_csv_data == {}
    clv.csv_data_shas()

    # take a copy of the cached data
    cached_csv_data = {**clv.cached_csv_data}
    assert clv.cached_csv_data["release"] == "dmd_test_20200101"
    assert (
        "download_data_fixed_headers_False_include_mapped_vmps_True"
        in clv.cached_csv_data
    )
    # 3 shas
    # - original
    # - mapped version, with fixed headers
    # - mapped version with fixed headers and extra original code column
    # - mapped version with all additional original columns
    assert len(clv.cached_csv_data["shas"]) == 4

    clv.csv_data = "code,term\n123,foo\n"
    clv.save()
    new_download_data = "code,term\r\n123,foo\r\n"
    # csv_data_for_download still returns the cached data
    assert clv.csv_data_for_download() != new_download_data
    assert (
        clv.csv_data_for_download()
        == cached_csv_data["download_data_fixed_headers_False_include_mapped_vmps_True"]
    )

    # make the release not the latest one so the data needs to be re-cached
    clv.cached_csv_data["release"] = "old"
    clv.save()
    assert clv.csv_data_for_download() == new_download_data
