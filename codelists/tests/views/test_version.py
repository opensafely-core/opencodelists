from django.urls import reverse

from builder.actions import save as save_for_review
from codelists.actions import publish_version
from codelists.models import Status

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


def test_medication_banner_only_on_published(client, dmd_version_asthma_medication):
    # The banner is not visible on an unpublished dm+d codelist version
    rsp = client.get(dmd_version_asthma_medication.get_absolute_url())
    assert rsp.status_code == 200
    assert b"Medication codelists can quickly become outdated" not in rsp.content

    # The banner is visible on a published dm+d codelist version
    publish_version(version=dmd_version_asthma_medication)
    rsp = client.get(dmd_version_asthma_medication.get_absolute_url())
    assert rsp.status_code == 200
    assert b"Medication codelists can quickly become outdated" in rsp.content


def test_medication_banner_only_on_medication(
    client, bnf_version_asthma, latest_published_version
):
    # The banner is not visible on a published SNOMED CT codelist (latest_published_version)
    rsp = client.get(latest_published_version.get_absolute_url())
    assert rsp.status_code == 200
    assert b"Medication codelists can quickly become outdated" not in rsp.content

    # The banner is visible on a published BNF codelist (bnf_version_asthma)
    rsp = client.get(bnf_version_asthma.get_absolute_url())
    assert rsp.status_code == 200
    assert b"Medication codelists can quickly become outdated" in rsp.content


def test_medication_banner_for_owner_of_codelist(client, bnf_version_asthma):
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
    bnf_draft_version = bnf_version_asthma.codelist.versions.filter(
        status=Status.DRAFT
    ).first()
    save_for_review(draft=bnf_draft_version)
    publish_version(version=bnf_draft_version)
    rsp = client.get(bnf_version_asthma.get_absolute_url())
    assert rsp.status_code == 200
    assert b"create your own" not in rsp.content
    assert b"create a new version" in rsp.content
    assert (
        b"there is already a draft version for this codelist which could be published"
        not in rsp.content
    )


def test_organisation_hyperlink_in_version_detail(client, organisation_codelist):
    """Test that organisation-owned codelists have a hyperlink to organisation index page."""
    # Get a published version of the organisation codelist
    version = organisation_codelist.latest_published_version()

    # Get the version detail page
    rsp = client.get(version.get_absolute_url())
    assert rsp.status_code == 200

    # Get the URL using Django's reverse
    org_url = reverse(
        "codelists:organisation_index",
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
