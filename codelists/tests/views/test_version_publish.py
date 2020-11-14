import pytest
from django.http import Http404

from codelists.views import version_publish
from opencodelists.tests.factories import UserFactory

from ..factories import CodelistFactory, create_draft_version, create_published_version
from .assertions import assert_post_redirects_to_login_page


def test_post_not_logged_in(rf):
    version = create_draft_version()
    assert_post_redirects_to_login_page(rf, version_publish, version)


def test_post_success(rf):
    version = create_draft_version()

    request = rf.post("/")
    request.user = UserFactory()
    response = version_publish(
        request,
        organisation_slug=version.codelist.organisation.slug,
        codelist_slug=version.codelist.slug,
        qualified_version_str=version.qualified_version_str,
    )

    assert response.status_code == 302

    version.refresh_from_db()

    assert response.url == version.get_absolute_url()
    assert not version.is_draft


def test_post_unknown_version(rf):
    codelist = CodelistFactory()

    request = rf.post("/")
    request.user = UserFactory()
    with pytest.raises(Http404):
        version_publish(
            request,
            organisation_slug=codelist.organisation.slug,
            codelist_slug=codelist.slug,
            qualified_version_str="test",
        )


def test_post_draft_mismatch(rf):
    version = create_published_version()

    # set the version string to that of a draft
    qualified_version_str = f"{version.qualified_version_str}-draft"

    request = rf.post("/")
    request.user = UserFactory()
    response = version_publish(
        request,
        organisation_slug=version.codelist.organisation.slug,
        codelist_slug=version.codelist.slug,
        qualified_version_str=qualified_version_str,
    )

    # we should get redirected to the Version page
    assert response.status_code == 302
    assert response.url == version.get_absolute_url()
