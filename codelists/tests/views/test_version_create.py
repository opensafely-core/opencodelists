from codelists.coding_systems import most_recent_database_alias

from ...models import Status
from .assertions import assert_post_unauthenticated, assert_post_unauthorised
from .helpers import force_login


def test_post_unauthenticated(client, version):
    assert_post_unauthenticated(client, version.get_create_url())


def test_post_unauthorised(client, version):
    assert_post_unauthorised(client, version.get_create_url())


def test_post_success(client, version):
    force_login(version, client)

    assert (
        version.codelist.versions.filter(
            author__isnull=False, status=Status.DRAFT
        ).exists()
        is False
    )
    response = client.post(
        version.get_create_url(),
        {"coding_system_database_alias": most_recent_database_alias("snomedct")},
    )

    draft = version.codelist.versions.get(author__isnull=False, status=Status.DRAFT)
    assert response.status_code == 302
    assert response.url == draft.get_builder_draft_url()


def test_post_success_no_coding_system_database_alias(client, version):
    force_login(version, client)

    assert (
        version.codelist.versions.filter(
            author__isnull=False, status=Status.DRAFT
        ).exists()
        is False
    )
    client.post(
        version.get_create_url(),
        {"coding_system_database_alias": ""},
    )

    draft = version.codelist.versions.get(author__isnull=False, status=Status.DRAFT)
    # defaults to most recent database alias for the version's coding system release
    assert draft.coding_system.database_alias == most_recent_database_alias("snomedct")


def test_post_unknown_code_status(client, version_with_complete_searches):
    version_with_complete_searches.codelist.versions.count()
    force_login(version_with_complete_searches, client)
    # delete a CodeObj that's included by a parent from the version to simulate a new concept
    # in the coding system; this will cause the export_to_builder function called from
    # the view to raise an error
    missing_implicit_concept = version_with_complete_searches.code_objs.filter(
        status="(+)"
    ).first()
    missing_implicit_concept.delete()

    response = client.post(
        version_with_complete_searches.get_create_url(),
        {"coding_system_database_alias": most_recent_database_alias("snomedct")},
    )
    # new version created
    draft = version_with_complete_searches.codelist.versions.get(
        author__isnull=False, status=Status.DRAFT
    )
    assert response.status_code == 302
    assert response.url == draft.get_builder_draft_url()
    # the new code has unknown status
    new_code = draft.code_objs.get(code=missing_implicit_concept.code)
    assert new_code.status == "?"
