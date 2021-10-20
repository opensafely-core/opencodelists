import pytest
from django.http import Http404

from codelists.views.decorators import load_codelist, load_owner, load_version

request = object()


def test_load_owner_for_organisation(organisation):
    assert owner_view(request, organisation_slug=organisation.slug) == organisation


def test_load_owner_for_user(user):
    assert owner_view(request, username=user.username) == user


def test_load_organisation_codelist(organisation_codelist):
    assert (
        codelist_view(
            request,
            organisation_slug=organisation_codelist.organisation.slug,
            codelist_slug=organisation_codelist.slug,
        )
        == organisation_codelist
    )


def test_load_user_codelist(user_codelist):
    assert (
        codelist_view(
            request,
            username=user_codelist.user.username,
            codelist_slug=user_codelist.slug,
        )
        == user_codelist
    )


def test_load_version_by_hash(version):
    assert (
        version_view(
            request,
            organisation_slug=version.codelist.organisation.slug,
            codelist_slug=version.codelist.slug,
            tag_or_hash=version.hash,
        )
        == version
    )


def test_load_version_by_tag(version):
    version.tag = "20210127"  # This tag looks like a hash
    version.save()

    assert (
        version_view(
            request,
            organisation_slug=version.codelist.organisation.slug,
            codelist_slug=version.codelist.slug,
            tag_or_hash=version.tag,
        )
        == version
    )


def test_load_version_with_tag_by_hash(version):
    version.tag = "20210127"  # This tag looks like a hash
    version.save()

    assert (
        version_view(
            request,
            organisation_slug=version.codelist.organisation.slug,
            codelist_slug=version.codelist.slug,
            tag_or_hash=version.hash,
        )
        == version
    )


def test_load_draft_version(draft_with_some_searches):
    draft = draft_with_some_searches

    rsp = version_view(
        request,
        organisation_slug=draft.codelist.organisation.slug,
        codelist_slug=draft.codelist.slug,
        tag_or_hash=draft.hash,
    )
    assert rsp.status_code == 302
    assert rsp.url == draft.get_builder_draft_url()


def test_load_owner_for_organisation_404():
    with pytest.raises(Http404):
        owner_view(request, organisation_slug="no-such-organisation")


def test_load_owner_for_user_404():
    with pytest.raises(Http404):
        owner_view(request, username="no-such-user")


def test_load_codelist_404(user):
    with pytest.raises(Http404):
        codelist_view(request, username=user.username, codelist_slug="no-such-codelist")


def test_version_codelist_404(user_codelist):
    with pytest.raises(Http404):
        version_view(
            request,
            username=user_codelist.user.username,
            codelist_slug=user_codelist.slug,
            tag_or_hash="no-such-tag",
        )


@load_owner
def owner_view(request, owner):
    return owner


@load_codelist
def codelist_view(request, codelist):
    return codelist


@load_version
def version_view(request, version):
    return version
