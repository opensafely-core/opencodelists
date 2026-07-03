import re

from bs4 import BeautifulSoup
from django.urls import reverse

from codelists.actions import create_codelist_with_codes
from codelists.models import Status
from coding_systems.icd10.known_diffs import (
    COMBINED_2016_VS_2019_DIFFERENCES,
    ReleaseTermDifference,
)

from .helpers import force_login


def test_get_old_style_version(client, old_style_version):
    rsp = client.get(old_style_version.get_absolute_url())
    assert rsp.status_code == 200


def test_get_version_with_no_searches(client, version_with_no_searches):
    rsp = client.get(version_with_no_searches.get_absolute_url())
    assert rsp.status_code == 200


def test_get_version_with_some_searches(client, version_with_some_searches):
    rsp = client.get(version_with_some_searches.get_absolute_url())
    assert rsp.status_code == 200


def test_get_version_with_complete_searches(client, version_with_complete_searches):
    rsp = client.get(version_with_complete_searches.get_absolute_url())
    assert rsp.status_code == 200


def test_get_user_version(client, user_version):
    rsp = client.get(user_version.get_absolute_url())
    assert rsp.status_code == 200


def test_get_user_has_edit_permissions(client, user, version_with_no_searches):
    client.force_login(user)
    rsp = client.get(version_with_no_searches.get_absolute_url())
    assert rsp.status_code == 200


def test_non_builder_compatible_coding_system(client, dmd_version_asthma_medication):
    rsp = client.get(dmd_version_asthma_medication.get_absolute_url())
    assert rsp.status_code == 200


def test_medication_banner_visible_for_outdated_coding_system_release(
    client,
    create_coding_system_release,
    dmd_version_asthma_medication,
    dmd_version_asthma_medication_published,
):
    """Test medication warning banner is shown for Under review and Published codelist versions that use an outdated coding system release."""

    # Create a newer dm+d release so the version used to build the codelists under test becomes outdated
    create_coding_system_release("dmd")

    # dmd_version_asthma_medication = Under Review.
    rsp = client.get(dmd_version_asthma_medication.get_absolute_url())
    assert rsp.status_code == 200
    assert b"Medication codelists can quickly become outdated" in rsp.content

    rsp = client.get(dmd_version_asthma_medication_published.get_absolute_url())
    assert rsp.status_code == 200
    assert b"Medication codelists can quickly become outdated" in rsp.content


def test_medication_banner_visible_with_dmd_or_bnf_coding_systems_only(
    client, create_coding_system_release, bnf_version_asthma, latest_published_version
):
    """Test medication warning banner is only visible for codelist versions that use a medication coding system"""

    # Create newer snomedct and bnf releases so the versions used to
    # build the codelists under test become outdated
    create_coding_system_release("snomedct")
    create_coding_system_release("bnf")

    rsp = client.get(latest_published_version.get_absolute_url())
    assert rsp.status_code == 200
    assert b"Medication codelists can quickly become outdated" not in rsp.content

    rsp = client.get(bnf_version_asthma.get_absolute_url())
    assert rsp.status_code == 200
    assert b"Medication codelists can quickly become outdated" in rsp.content


def test_medication_banner_not_visible_for_current_coding_system_release(
    client, bnf_version_asthma
):
    """Test medication warning banner is not shown when a codelist version uses the current coding system release"""

    rsp = client.get(bnf_version_asthma.get_absolute_url())
    assert rsp.status_code == 200
    assert b"Medication codelists can quickly become outdated" not in rsp.content


def test_medication_banner_for_owner_of_codelist(
    client,
    create_coding_system_release,
    bnf_version_asthma,
    dmd_version_asthma_medication,
):
    # Create newer BNF and dm+d releases so the meds banner is shown.
    create_coding_system_release("bnf")
    create_coding_system_release("dmd")

    # If you can't create a new version (not the owner or in the org) then you
    # are offered to "create your own" rather than "create a new version"
    rsp = client.get(bnf_version_asthma.get_absolute_url())
    assert rsp.status_code == 200
    assert b"create your own" in rsp.content
    assert b"create a new version" not in rsp.content

    # If you can create a new version (the owner or in the org), but there is
    # already a draft version, then you are told about this
    force_login(bnf_version_asthma, client)
    rsp = client.get(bnf_version_asthma.get_absolute_url())
    assert rsp.status_code == 200
    assert b"create your own" not in rsp.content
    assert (
        b"there is already a draft version for this codelist which could be published"
        in rsp.content
    )

    # If you can create a new version (the owner or in the org), and there is
    # not already a draft version, then you are invited to "create a new version"
    rsp = client.get(dmd_version_asthma_medication.get_absolute_url())
    assert rsp.status_code == 200
    assert b"create your own" not in rsp.content
    assert b"create a new version" in rsp.content
    assert (
        b"there is already a draft version for this codelist which could be published"
        not in rsp.content
    )


def test_icd10_known_differences_data(client, icd10_data, monkeypatch, organisation):
    monkeypatch.setitem(
        COMBINED_2016_VS_2019_DIFFERENCES,
        "M770",
        ReleaseTermDifference(
            combined_2016="Old term",
            who_2019="New term",
            clinically_equivalent=False,
        ),
    )
    monkeypatch.setitem(
        COMBINED_2016_VS_2019_DIFFERENCES,
        "M771",
        ReleaseTermDifference(
            combined_2016="Other old term",
            who_2019="Other new term",
            clinically_equivalent=False,
        ),
    )
    codelist = create_codelist_with_codes(
        owner=organisation,
        name="ICD10 known differences",
        coding_system_id="icd10",
        codes=["M770", "M771"],
        coding_system_database_alias="icd10_test_20200101",
        status=Status.PUBLISHED,
    )

    rsp = client.get(codelist.latest_published_version().get_absolute_url())

    assert rsp.status_code == 200
    assert rsp.context["icd10_term_differences"] == {
        "M770": {
            "combined_2016": "Old term",
            "who_2019": "New term",
        },
        "M771": {
            "combined_2016": "Other old term",
            "who_2019": "Other new term",
        },
    }


def test_icd10_known_differences_banner_is_icd10_only(
    client, latest_published_version, monkeypatch
):
    monkeypatch.setitem(
        COMBINED_2016_VS_2019_DIFFERENCES,
        "202855006",
        ReleaseTermDifference(
            combined_2016="Old term",
            who_2019="New term",
            clinically_equivalent=False,
        ),
    )

    rsp = client.get(latest_published_version.get_absolute_url())

    assert rsp.status_code == 200
    assert rsp.context["icd10_term_differences"] == []


def test_icd10_moved_code_sets_data(client, icd10_data, monkeypatch, organisation):
    monkeypatch.setattr(
        "coding_systems.icd10.known_diffs.MOVED_CODE_SETS",
        (
            {
                "title": "Test moved concept",
                "nhs2016": ["M770"],
                "who2019": ["M771"],
                "comment": "",
            },
        ),
    )
    codelist = create_codelist_with_codes(
        owner=organisation,
        name="ICD10 moved codes",
        coding_system_id="icd10",
        codes=["M770"],
        coding_system_database_alias="icd10_test_20200101",
        status=Status.PUBLISHED,
    )

    rsp = client.get(codelist.latest_published_version().get_absolute_url())

    assert rsp.status_code == 200
    assert {
        "comment": "",
        "title": "Test moved concept",
        "nhs2016": ["M770"],
        "who2019": ["M771"],
    } in rsp.context["icd10_moved_codes"]


def test_organisation_hyperlink_in_version_detail(client, organisation_codelist):
    """Test that organisation-owned codelists have a hyperlink to organisation published page."""
    # Get a published version of the organisation codelist
    version = organisation_codelist.latest_published_version()

    # Get the version detail page
    rsp = client.get(version.get_absolute_url())
    assert rsp.status_code == 200

    # Get the URL using Django's reverse
    org_url = reverse(
        "codelists:organisation_published",
        kwargs={"organisation_slug": organisation_codelist.organisation.slug},
    )

    # Check url exists
    assert f'href="{org_url}"'.encode() in rsp.content
    assert organisation_codelist.organisation.name.encode() in rsp.content


def test_author_hyperlink_in_version_detail(client, user_codelist):
    """Test that user-owned codelists have a hyperlink to author's page."""
    # Get a published version of the user codelist
    version = user_codelist.latest_published_version()

    # Get the version detail page
    rsp = client.get(version.get_absolute_url())
    assert rsp.status_code == 200

    # Get the URL using Django's reverse
    user_url = reverse("user", kwargs={"username": user_codelist.user.username})

    # Check url exists
    assert f'href="{user_url}"'.encode() in rsp.content
    assert user_codelist.user.name.encode() in rsp.content


def test_download_disabled_for_codelist_author_for_undownloadable_version(
    client, organisation_user, null_codelist
):
    """Test that the download CSV button is disabled for codelist authors
    when the codelist is not downloadable."""
    version = null_codelist.versions.first()
    version.csv_data = "header,without,correct,columns\n1,2,3,4\n5,6,7,8"
    version.save()

    client.force_login(organisation_user)

    rsp = client.get(version.get_absolute_url())
    assert rsp.status_code == 200

    # The button (and tooltip) is present...
    assert b"Download CSV" in rsp.content
    assert b"This codelist cannot be downloaded" in rsp.content

    # ...but disabled
    content = rsp.content.decode("utf-8")
    disabled_csv_pattern = r"disabled[^>]*>\s*Download CSV"
    assert re.search(disabled_csv_pattern, content, re.DOTALL)


def test_download_not_visible_for_non_codelist_for_undownloadable_version(
    client, null_codelist
):
    """Test that the download CSV button is not visible for non-codelist authors."""
    version = null_codelist.versions.first()
    version.csv_data = "header,without,correct,columns\n1,2,3,4\n5,6,7,8"
    version.save()

    rsp = client.get(version.get_absolute_url())
    assert rsp.status_code == 200

    # The button and tooltip are not present
    assert b"Download CSV" not in rsp.content
    assert b"This codelist cannot be downloaded" not in rsp.content


def test_clone_hyperlink_in_organisation_published_version_detail(
    client, new_style_codelist
):
    version = new_style_codelist.latest_published_version()

    # Get the version detail page
    rsp = client.get(version.get_absolute_url())
    assert rsp.status_code == 200

    clone_url = version.codelist.get_clone_url()

    # Check url exists
    assert f'href="{clone_url}"'.encode() in rsp.content


def test_clone_hyperlink_in_user_published_version_detail(client, user_codelist):
    version = user_codelist.latest_published_version()

    # Get the version detail page
    rsp = client.get(version.get_absolute_url())
    assert rsp.status_code == 200

    clone_url = version.codelist.get_clone_url()

    # Check url exists
    assert f'href="{clone_url}"'.encode() in rsp.content


def test_clone_hyperlink_not_in_draft_version_detail(client, minimal_draft):
    # Get the version detail page (redirected)
    rsp = client.get(minimal_draft.get_absolute_url())
    assert rsp.status_code == 302

    clone_url = minimal_draft.codelist.get_clone_url()

    # Check url exists
    assert f'href="{clone_url}"'.encode() not in rsp.content


def test_clone_hyperlink_not_in_under_review_version_detail(
    client, version_under_review
):
    # Get the version detail page
    rsp = client.get(version_under_review.get_absolute_url())
    assert rsp.status_code == 200

    clone_url = version_under_review.codelist.get_clone_url()

    # Check url exists
    assert f'href="{clone_url}"'.encode() not in rsp.content


def test_clone_hyperlink_in_editable_under_review_detail(
    client, version_under_review, organisation_user
):
    force_login(organisation_user, client)

    # Get the version detail page
    rsp = client.get(version_under_review.get_absolute_url())
    assert rsp.status_code == 200

    clone_url = version_under_review.codelist.get_clone_url()

    # Check url exists
    assert f'href="{clone_url}"'.encode() in rsp.content


def test_under_review_version_visible_in_sidebar_for_non_editor(
    client, version_under_review, latest_published_version, user_without_organisation
):
    force_login(user_without_organisation, client)

    rsp = client.get(version_under_review.get_absolute_url())
    assert rsp.status_code == 200

    parsed_html = BeautifulSoup(rsp.content, "html.parser")
    versions_section = parsed_html.find("section", id="versions")
    assert versions_section

    section_text = versions_section.get_text(" ", strip=True)
    assert version_under_review.tag_or_hash in section_text
    assert latest_published_version.tag_or_hash in section_text
