import hashlib
import json
from datetime import datetime

import pytest
from django.db import connection

from codelists.actions import update_codelist
from codelists.models import Codelist, Handle
from mappings.dmdvmpprevmap.models import Mapping as VmpPrevMapping
from opencodelists.tests.assertions import assert_difference, assert_no_difference


def test_codelists_get(client, organisation):
    rsp = client.get(
        f"/api/v1/codelist/{organisation.slug}/?description&methodology&references"
    )
    data = json.loads(rsp.content)
    assert rsp.status_code == 200

    today = datetime.today().date().isoformat()
    assert data["codelists"] == [
        {
            "full_slug": "test-university/bnf-codelist",
            "slug": "bnf-codelist",
            "name": "BNF Codelist",
            "coding_system_id": "bnf",
            "organisation": "Test University",
            "user": "",
            "description": None,
            "methodology": None,
            "references": [
                {"text": "Reference 1", "url": "https://example.com/reference1"},
                {"text": "Reference 2", "url": "https://example.com/reference2"},
            ],
            "versions": [
                {
                    "hash": "5093d98b",
                    "tag": None,
                    "full_slug": "test-university/bnf-codelist/5093d98b",
                    "status": "published",
                    "downloadable": True,
                    "updated_date": today,
                },
                {
                    "hash": "37846656",
                    "tag": None,
                    "full_slug": "test-university/bnf-codelist/37846656",
                    "status": "draft",
                    "downloadable": False,
                    "updated_date": today,
                },
            ],
        },
        {
            "full_slug": "test-university/codelist-from-scratch",
            "slug": "codelist-from-scratch",
            "name": "Codelist From Scratch",
            "organisation": "Test University",
            "user": "",
            "description": None,
            "methodology": None,
            "references": [],
            "coding_system_id": "snomedct",
            "versions": [
                {
                    "hash": "53469981",
                    "tag": None,
                    "full_slug": "test-university/codelist-from-scratch/53469981",
                    "status": "draft",
                    "downloadable": False,
                    "updated_date": today,
                }
            ],
        },
        {
            "full_slug": "test-university/dmd-codelist",
            "slug": "dmd-codelist",
            "name": "DMD Codelist",
            "coding_system_id": "dmd",
            "organisation": "Test University",
            "user": "",
            "description": "What this is",
            "methodology": "How we did it",
            "references": [],
            "versions": [
                {
                    "hash": "34d1a660",
                    "tag": None,
                    "full_slug": "test-university/dmd-codelist/34d1a660",
                    "status": "under review",
                    "downloadable": True,
                    "updated_date": today,
                },
                {
                    "hash": "1bc2332b",
                    "tag": None,
                    "full_slug": "test-university/dmd-codelist/1bc2332b",
                    "status": "under review",
                    "downloadable": True,
                    "updated_date": today,
                },
                {
                    "hash": "02b2bff6",
                    "tag": None,
                    "full_slug": "test-university/dmd-codelist/02b2bff6",
                    "status": "under review",
                    "downloadable": True,
                    "updated_date": today,
                },
                {
                    "hash": "69a34cc0",
                    "tag": None,
                    "full_slug": "test-university/dmd-codelist/69a34cc0",
                    "status": "under review",
                    "downloadable": False,
                    "updated_date": today,
                },
            ],
        },
        {
            "full_slug": "test-university/minimal-codelist",
            "slug": "minimal-codelist",
            "name": "Minimal Codelist",
            "organisation": "Test University",
            "user": "",
            "description": None,
            "methodology": None,
            "references": [],
            "coding_system_id": "snomedct",
            "versions": [
                {
                    "hash": "08183fe2",
                    "tag": None,
                    "full_slug": "test-university/minimal-codelist/08183fe2",
                    "status": "published",
                    "downloadable": True,
                    "updated_date": today,
                },
                {
                    "hash": "6f08ccac",
                    "tag": None,
                    "full_slug": "test-university/minimal-codelist/6f08ccac",
                    "status": "draft",
                    "downloadable": False,
                    "updated_date": today,
                },
            ],
        },
        {
            "full_slug": "test-university/new-style-codelist",
            "slug": "new-style-codelist",
            "name": "New-style Codelist",
            "organisation": "Test University",
            "user": "",
            "description": None,
            "methodology": None,
            "references": [
                {"text": "Reference 1", "url": "https://example.com/reference1"},
                {"text": "Reference 2", "url": "https://example.com/reference2"},
            ],
            "coding_system_id": "snomedct",
            "versions": [
                {
                    "hash": "1e74f321",
                    "tag": None,
                    "full_slug": "test-university/new-style-codelist/1e74f321",
                    "status": "published",
                    "downloadable": True,
                    "updated_date": today,
                },
                {
                    "hash": "05657fec",
                    "tag": None,
                    "full_slug": "test-university/new-style-codelist/05657fec",
                    "status": "under review",
                    "downloadable": True,
                    "updated_date": today,
                },
                {
                    "hash": "6c560cb6",
                    "tag": None,
                    "full_slug": "test-university/new-style-codelist/6c560cb6",
                    "status": "under review",
                    "downloadable": True,
                    "updated_date": today,
                },
            ],
        },
        {
            "full_slug": "test-university/null-codelist",
            "slug": "null-codelist",
            "name": "Null Codelist",
            "coding_system_id": "null",
            "organisation": "Test University",
            "user": "",
            "description": "",
            "methodology": "",
            "references": [],
            "versions": [
                {
                    "hash": "55f95977",
                    "tag": None,
                    "full_slug": "test-university/null-codelist/55f95977",
                    "status": "under review",
                    "downloadable": True,
                    "updated_date": today,
                },
                {
                    "hash": "3ce9e642",
                    "tag": None,
                    "full_slug": "test-university/null-codelist/3ce9e642",
                    "status": "under review",
                    "downloadable": True,
                    "updated_date": today,
                },
            ],
        },
        {
            "full_slug": "test-university/old-style-codelist",
            "slug": "old-style-codelist",
            "name": "Old-style Codelist",
            "organisation": "Test University",
            "user": "",
            "description": "What this is",
            "methodology": "How we did it",
            "references": [],
            "coding_system_id": "snomedct",
            "versions": [
                {
                    "hash": "66f08cca",
                    "tag": None,
                    "full_slug": "test-university/old-style-codelist/66f08cca",
                    "status": "under review",
                    "downloadable": True,
                    "updated_date": today,
                },
                {
                    "hash": "4de11995",
                    "tag": None,
                    "full_slug": "test-university/old-style-codelist/4de11995",
                    "status": "under review",
                    "downloadable": True,
                    "updated_date": today,
                },
            ],
        },
    ]


def test_codelists_get_all(client, organisation, organisation_user):
    rsp = client.get("/api/v1/codelist/?include-users")
    data = json.loads(rsp.content)
    assert rsp.status_code == 200

    # all org codelist fixtures are owned by the same organisation
    organisations = {
        cl["organisation"] for cl in data["codelists"] if cl["organisation"]
    }
    assert organisations == {organisation.name}

    user_codelists = [cl for cl in data["codelists"] if cl["user"]]
    assert len(user_codelists) == 2  # user-codelist-from-scratch, user-owned-codelist
    assert {cl["user"] for cl in user_codelists} == {organisation_user.username}


def test_codelists_get_all_still_works_for_a_codelist_with_a_missing_handle(
    client,
    organisation,
    organisation_user,
):
    # See issue #2731.
    # We found a Codelist without an associated Handle,
    # which broke this API endpoint.

    # Delete the Handle for one codelist. Via SQL as we disallow via ORM.
    codelist_to_break = Codelist.objects.get(handles__name="User Codelist From Scratch")
    table = Handle._meta.db_table
    with connection.cursor() as cursor:
        cursor.execute(
            f'DELETE FROM "{table}" WHERE id = {codelist_to_break.current_handle.pk}'
        )

    rsp = client.get("/api/v1/codelist/?include-users")
    assert rsp.status_code == 200


def test_codelists_get_with_coding_system_id(client, organisation):
    rsp = client.get(f"/api/v1/codelist/{organisation.slug}/?coding_system_id=snomedct")
    data = json.loads(rsp.content)
    assert len(data["codelists"]) == 4

    rsp = client.get(f"/api/v1/codelist/{organisation.slug}/?coding_system_id=")
    data = json.loads(rsp.content)
    assert len(data["codelists"]) == 7

    rsp = client.get(f"/api/v1/codelist/{organisation.slug}/?coding_system_id=bnf")
    data = json.loads(rsp.content)
    assert len(data["codelists"]) == 1


def test_codelists_get_exclude_previous_owner(
    client, organisation, dmd_codelist, another_organisation
):
    rsp = client.get(f"/api/v1/codelist/{organisation.slug}/?coding_system_id=dmd")
    data = json.loads(rsp.content)
    assert len(data["codelists"]) == 1

    # change the codelist's owner
    update_codelist(
        codelist=dmd_codelist,
        owner=another_organisation,
        name=dmd_codelist.name,
        slug=dmd_codelist.slug,
        description=dmd_codelist.description,
        methodology=dmd_codelist.methodology,
        references={},
        signoffs={},
    )

    # dmd codelists is still one of the original organisation's codelists
    assert dmd_codelist in organisation.codelists
    # but the current owner is another_organisation
    assert dmd_codelist.owner == another_organisation

    rsp = client.get(f"/api/v1/codelist/{organisation.slug}/?coding_system_id=dmd")
    data = json.loads(rsp.content)
    assert len(data["codelists"]) == 0


def test_org_codelist_with_two_handles_is_included(client, organisation, dmd_codelist):
    """When an organisation codelist has two Handles it should still appear
    in the organisation codelists API response.

    Regression test for a case where duplicate handles caused the API to
    exclude the codelist entirely.
    """
    rsp = client.get(f"/api/v1/codelist/{organisation.slug}/")
    assert rsp.status_code == 200
    data = json.loads(rsp.content)
    num_codelists = len(data["codelists"])
    # Create an additional handle for the same codelist using the public
    # update path so we exercise the application's handle-creation logic.
    update_codelist(
        codelist=dmd_codelist,
        owner=organisation,
        name=f"{dmd_codelist.name} Alt",
        slug=f"{dmd_codelist.slug}-alt",
        description=dmd_codelist.description,
        methodology=dmd_codelist.methodology,
        references={},
        signoffs={},
    )

    rsp = client.get(f"/api/v1/codelist/{organisation.slug}/")
    assert rsp.status_code == 200
    data = json.loads(rsp.content)

    expected_full_slug = f"{organisation.slug}/{dmd_codelist.slug}"
    assert any(cl["full_slug"] == expected_full_slug for cl in data["codelists"]), (
        "Expected codelist with two handles to appear in API response"
    )
    # Ensure the original codelist is still present
    assert len(data["codelists"]) == num_codelists


def test_codelists_get_with_no_organisation(client, organisation):
    rsp = client.get("/api/v1/codelist/?coding_system_id=snomedct&include-users")
    data = json.loads(rsp.content)
    user_codelists = [
        cl for cl in data["codelists"] if cl["full_slug"].startswith("user")
    ]
    assert len(user_codelists) == 2
    for user_codelist in user_codelists:
        assert user_codelist["organisation"] == ""


def test_codelists_get_with_tag(client, universe):
    rsp = client.get("/api/v1/codelist/?tag=new-style")
    data = json.loads(rsp.content)
    assert len(data["codelists"]) == 2


def test_codelists_get_with_tag_and_include_users(client, universe):
    rsp = client.get("/api/v1/codelist/?tag=new-style&include-users")
    data = json.loads(rsp.content)
    assert len(data["codelists"]) == 4


def test_codelists_post(client, user):
    data = {
        "name": "New codelist",
        "coding_system_id": "snomedct",
        "coding_system_database_alias": "snomedct_test_20200101",
        "codes": ["128133004", "156659008"],
    }

    with assert_difference(user.codelists.count, expected_difference=1):
        rsp = post(client, user.get_codelists_api_url(), data, user)

    assert rsp.status_code == 200


def test_codelists_post_no_auth(client, user):
    data = {
        "name": "New codelist",
        "coding_system_id": "snomedct",
        "coding_system_database_alias": "snomedct_test_20200101",
        "codes": ["128133004", "156659008"],
    }

    with assert_no_difference(user.codelists.count):
        rsp = post(client, user.get_codelists_api_url(), data, None)

    assert rsp.status_code == 401


def test_codelists_post_permission_denied(client, user, user_without_organisation):
    data = {
        "name": "New codelist",
        "coding_system_id": "snomedct",
        "coding_system_database_alias": "snomedct_test_20200101",
        "codes": ["128133004", "156659008"],
    }

    with assert_no_difference(user.codelists.count):
        rsp = post(
            client, user.get_codelists_api_url(), data, user_without_organisation
        )

    assert rsp.status_code == 403


def test_versions_post_codes(client, user, user_codelist):
    data = {
        "codes": ["128133004", "156659008"],
        "coding_system_database_alias": "snomedct_test_20200101",
    }

    with assert_difference(user_codelist.versions.count, expected_difference=1):
        rsp = post(client, user_codelist.get_versions_api_url(), data, user)

    assert rsp.status_code == 200


def test_versions_post_codes_with_no_force_new_version(client, user, user_codelist):
    data = {
        "name": "New codelist",
        "coding_system_id": "snomedct",
        "coding_system_database_alias": "snomedct_test_20200101",
        "codes": ["128133004", "156659008"],
    }
    post(client, user_codelist.get_versions_api_url(), data, user)

    same_data = {
        "name": "New codelist",
        "coding_system_database_alias": "snomedct_test_20200101",
        "codes": ["128133004", "156659008"],
        "always_create_new_version": False,
    }
    with assert_no_difference(user_codelist.versions.count):
        rsp = post(client, user_codelist.get_versions_api_url(), same_data, user)

    assert rsp.status_code == 400


def test_versions_post_codes_with_force_new_version(client, user, user_codelist):
    data = {
        "name": "New codelist",
        "coding_system_id": "snomedct",
        "coding_system_database_alias": "snomedct_test_20200101",
        "codes": ["128133004", "156659008"],
    }
    post(client, user_codelist.get_versions_api_url(), data, user)

    same_data = {
        "name": "New codelist",
        "coding_system_database_alias": "snomedct_test_20200101",
        "codes": ["128133004", "156659008"],
        "always_create_new_version": True,
    }
    with assert_difference(user_codelist.versions.count, expected_difference=1):
        rsp = post(client, user_codelist.get_versions_api_url(), same_data, user)

    assert rsp.status_code == 200


def test_versions_post_ecl(client, user, user_codelist):
    data = {
        "ecl": "<<128133004 OR 156659008",
        "coding_system_database_alias": "snomedct_test_20200101",
    }

    with assert_difference(user_codelist.versions.count, expected_difference=1):
        rsp = post(client, user_codelist.get_versions_api_url(), data, user)

    assert rsp.status_code == 200


def test_versions_post_no_difference(client, user, user_codelist):
    data = {
        "ecl": "(<<128133004 OR 156659008) MINUS <<439656005",
        "coding_system_database_alias": "snomedct_test_20200101",
    }

    with assert_no_difference(user_codelist.versions.count):
        rsp = post(client, user_codelist.get_versions_api_url(), data, user)

    assert rsp.status_code == 400
    assert json.loads(rsp.content) == {"error": "No difference to previous version"}


def test_versions_post_bad_ecl(client, user, user_codelist):
    data = {
        "ecl": "<<128133004 MIN",
        "coding_system_database_alias": "snomedct_test_20200101",
    }

    with assert_no_difference(user_codelist.versions.count):
        rsp = post(client, user_codelist.get_versions_api_url(), data, user)

    assert rsp.status_code == 400
    assert json.loads(rsp.content)["error"].startswith("InputMismatchException")


def test_versions_post_missing_data(client, user, user_codelist):
    data = {}

    with assert_no_difference(user_codelist.versions.count):
        rsp = post(client, user_codelist.get_versions_api_url(), data, user)

    assert rsp.status_code == 400
    assert json.loads(rsp.content) == {
        "error": "Provide exactly one of `codes`, `csv_data` or `ecl`"
    }


def test_versions_post_no_auth(client, user_codelist):
    data = {
        "ecl": "<<128133004",
        "coding_system_database_alias": "snomedct_test_20200101",
    }

    with assert_no_difference(user_codelist.versions.count):
        rsp = post(client, user_codelist.get_versions_api_url(), data, None)

    assert rsp.status_code == 401


def test_versions_post_permission_denied(
    client, user_without_organisation, user_codelist
):
    data = {
        "ecl": "<<128133004",
        "coding_system_database_alias": "snomedct_test_20200101",
    }

    with assert_no_difference(user_codelist.versions.count):
        rsp = post(
            client,
            user_codelist.get_versions_api_url(),
            data,
            user_without_organisation,
        )

    assert rsp.status_code == 403


def post(client, url, data, user):
    if user is None:
        headers = {}
    else:
        headers = {"HTTP_AUTHORIZATION": f"Token {user.api_token}"}
    return client.post(url, data, content_type="application/json", **headers)


@pytest.mark.parametrize(
    "codelists,manifest,error",
    [
        ("user/foo/codelist-foo/1234", "[foo]", "Codelists manifest file is invalid"),
        (
            "user/foo/codelist-foo/1234",
            '{"files": {"id": "user/foo/codelist-foo/1234", "sha": "bar"}}',
            "user/foo/codelist-foo/1234 could not be found",
        ),
        (
            "foo/codelist-foo/1234",
            '{"files": {"id": "foo/codelist-foo/1234", "sha": "bar"}}',
            "foo/codelist-foo/1234 could not be found",
        ),
        (
            "foo/bar/codelist-foo/1234/",
            '{"files": {"id": "foo/bar/codelist-foo/1234", "sha": "bar"}}',
            "foo/bar/codelist-foo/1234 does not match expected codelist pattern",
        ),
    ],
)
def test_codelists_check_bad_input_files(client, codelists, manifest, error):
    data = {"codelists": codelists, "manifest": manifest}
    resp = client.post("/api/v1/check/", data)
    assert resp.json() == {"status": "error", "data": {"error": error}}


def test_codelists_check_new_style_codelist_version(
    client, user_version, new_style_version
):
    user_codelist_id = f"user/{user_version.user.username}/{user_version.codelist.slug}/{user_version.hash}"
    user_codelist_csv_id = user_codelist_id.replace("/", "-") + ".csv"
    org_codelist_id = f"{new_style_version.organisation.slug}/{new_style_version.codelist.slug}/{new_style_version.hash}"
    org_codelist_csv_id = org_codelist_id.replace("/", "-") + ".csv"
    manifest = {
        "files": {
            user_codelist_csv_id: {
                "id": user_codelist_id,
                "url": f"https://opencodelist.org/codelists/{user_codelist_id}/",
                "downloaded_at": "2023-10-04 13:55:17.569997Z",
                "sha": user_version.csv_data_sha(),
            },
            org_codelist_csv_id: {
                "id": org_codelist_id,
                "url": f"https://opencodelist.org/codelists/{org_codelist_id}/",
                "downloaded_at": "2023-10-04 13:55:17.569997Z",
                "sha": new_style_version.csv_data_sha(),
            },
        }
    }
    data = {
        "codelists": f"# this is a comment line\n{user_codelist_id}\n{org_codelist_id}/\n\n",
        "manifest": json.dumps(manifest),
    }
    resp = client.post("/api/v1/check/", data)
    assert resp.json() == {"status": "ok"}


def test_codelists_check_old_style_codelist_version(client, old_style_version):
    codelist_id = f"{old_style_version.organisation.slug}/{old_style_version.codelist.slug}/{old_style_version.hash}"
    codelist_csv_id = codelist_id.replace("/", "-") + ".csv"
    manifest = {
        "files": {
            codelist_csv_id: {
                "id": codelist_id,
                "url": f"https://opencodelist.org/codelists/{codelist_id}/",
                "downloaded_at": "2023-10-04 13:55:17.569997Z",
                "sha": old_style_version.csv_data_sha(),
            }
        }
    }
    data = {"codelists": codelist_id, "manifest": json.dumps(manifest)}
    resp = client.post("/api/v1/check/", data)
    assert resp.json() == {"status": "ok"}


@pytest.mark.parametrize(
    "tag,expected_status",
    [("v1", "ok"), ("V-1", "ok"), ("v.1.1", "ok"), ("v1&2", "ok"), ("v1/2", "error")],
)
def test_codelists_check_codelist_with_tag(
    client, old_style_version, tag, expected_status
):
    old_style_version.tag = tag
    old_style_version.save()

    codelist_id = (
        f"{old_style_version.organisation.slug}/{old_style_version.codelist.slug}/{tag}"
    )
    codelist_csv_id = codelist_id.replace("/", "-") + ".csv"
    manifest = {
        "files": {
            codelist_csv_id: {
                "id": codelist_id,
                "url": f"https://opencodelist.org/codelists/{codelist_id}/",
                "downloaded_at": "2023-10-04 13:55:17.569997Z",
                "sha": old_style_version.csv_data_sha(),
            }
        }
    }
    data = {"codelists": codelist_id, "manifest": json.dumps(manifest)}
    resp = client.post("/api/v1/check/", data)
    assert resp.json()["status"] == expected_status


def test_codelists_check_has_added_codelists(
    client, user_version, version_with_no_searches
):
    user_codelist_id = f"user/{user_version.user.username}/{user_version.codelist.slug}/{user_version.hash}"
    user_codelist_csv_id = user_codelist_id.replace("/", "-") + ".csv"
    org_codelist_id = (
        f"{version_with_no_searches.organisation.slug}/"
        f"{version_with_no_searches.codelist.slug}/"
        f"{version_with_no_searches.hash}"
    )
    # Setup: Study repo has added a codelist (version_with_no_searches) in the codelists.txt file,
    # but has not run update, so manifest only contains one codelist
    manifest = {
        "files": {
            user_codelist_csv_id: {
                "id": user_codelist_id,
                "url": f"https://opencodelist.org/codelists/{user_codelist_id}/",
                "downloaded_at": "2023-10-04 13:55:17.569997Z",
                "sha": user_version.csv_data_sha(),
            },
        }
    }
    data = {
        "codelists": f"# this is a comment line\n{user_codelist_id}\n{org_codelist_id}/\n\n",
        "manifest": json.dumps(manifest),
    }
    resp = client.post("/api/v1/check/", data)
    assert resp.json() == {
        "status": "error",
        "data": {"added": [org_codelist_id], "removed": [], "changed": []},
    }


def test_codelists_check_has_removed_codelists(
    client, user_version, version_with_no_searches
):
    user_codelist_id = f"user/{user_version.user.username}/{user_version.codelist.slug}/{user_version.hash}"
    user_codelist_csv_id = user_codelist_id.replace("/", "-") + ".csv"
    org_codelist_id = (
        f"{version_with_no_searches.organisation.slug}/"
        f"{version_with_no_searches.codelist.slug}/"
        f"{version_with_no_searches.hash}"
    )
    org_codelist_csv_id = org_codelist_id.replace("/", "-") + ".csv"

    # Setup: Study repo has remove a codelist (version_with_no_searches) in the codelists.txt file,
    # but has not run update, so manifest contains 2 codelists, codelists.txt contains only one
    manifest = {
        "files": {
            user_codelist_csv_id: {
                "id": user_codelist_id,
                "url": f"https://opencodelist.org/codelists/{user_codelist_id}/",
                "downloaded_at": "2023-10-04 13:55:17.569997Z",
                "sha": user_version.csv_data_sha(),
            },
            org_codelist_csv_id: {
                "id": org_codelist_id,
                "url": f"https://opencodelist.org/codelists/{org_codelist_id}/",
                "downloaded_at": "2023-10-04 13:55:17.569997Z",
                "sha": version_with_no_searches.csv_data_sha(),
            },
        }
    }
    data = {"codelists": user_codelist_id, "manifest": json.dumps(manifest)}
    resp = client.post("/api/v1/check/", data)
    assert resp.json() == {
        "status": "error",
        "data": {"added": [], "removed": [org_codelist_id], "changed": []},
    }


def test_codelists_check_changes(client, dmd_version_asthma_medication):
    codelist_id = (
        f"{dmd_version_asthma_medication.organisation.slug}/"
        f"{dmd_version_asthma_medication.codelist.slug}/"
        f"{dmd_version_asthma_medication.hash}"
    )
    codelist_csv_id = codelist_id.replace("/", "-") + ".csv"

    # Test the happy path for this dmd version
    manifest = {
        "files": {
            codelist_csv_id: {
                "id": codelist_id,
                "url": f"https://opencodelist.org/codelists/{codelist_csv_id}/",
                "downloaded_at": "2023-10-04 13:55:17.569997Z",
                "sha": dmd_version_asthma_medication.csv_data_sha(),
            },
        }
    }
    data = {"codelists": codelist_id, "manifest": json.dumps(manifest)}
    resp = client.post("/api/v1/check/", data)
    assert resp.json() == {"status": "ok"}

    # mock cache to be related to an older release
    dmd_version_asthma_medication.cached_csv_data["release"] = "old"
    dmd_version_asthma_medication.save()
    # Add a VMP mapping which will be added into the CSV download
    VmpPrevMapping.objects.create(id="10514511000001106", vpidprev="999")
    resp = client.post("/api/v1/check/", data)

    assert resp.json() == {
        "status": "error",
        "data": {"added": [], "removed": [], "changed": [codelist_id]},
    }


@pytest.mark.parametrize(
    "downloaded_data",
    [
        (  # default download (as expected from a current `opensafely codelists update`)
            "code,term,dmd_id\r\n"
            "10514511000001106,Adrenaline (base) 220micrograms/dose inhaler,10514511000001106\r\n"
            "10525011000001107,Adrenaline (base) 220micrograms/dose inhaler refill,10525011000001107\r\n"
        ),
        (  # old-style download (from before VMPs were mapped into dmd downloads)
            "dmd_type,dmd_id,dmd_name,bnf_code\r\n"
            "VMP,10514511000001106,Adrenaline (base) 220micrograms/dose inhaler,0301012A0AAABAB\r\n"
            "VMP,10525011000001107,Adrenaline (base) 220micrograms/dose inhaler refill,0301012A0AAACAC\r\n"
        ),
        (  # download excluding original code column
            "code,term\r\n"
            "10514511000001106,Adrenaline (base) 220micrograms/dose inhaler\r\n"
            "10525011000001107,Adrenaline (base) 220micrograms/dose inhaler refill\r\n"
        ),
    ],
)
def test_codelists_check_dmd_alternative_downloads(
    client, dmd_version_asthma_medication, downloaded_data
):
    # Test that any of these versions of a downloaded CSV are
    # still considered OK
    codelist_id = (
        f"{dmd_version_asthma_medication.organisation.slug}/"
        f"{dmd_version_asthma_medication.codelist.slug}/"
        f"{dmd_version_asthma_medication.hash}"
    )
    codelist_csv_id = codelist_id.replace("/", "-") + ".csv"

    manifest = {
        "files": {
            codelist_csv_id: {
                "id": codelist_id,
                "url": f"https://opencodelist.org/codelists/{codelist_csv_id}/",
                "downloaded_at": "2023-10-04 13:55:17.569997Z",
                "sha": dmd_version_asthma_medication.csv_data_sha(
                    csv_data=downloaded_data
                ),
            },
        }
    }
    data = {"codelists": codelist_id, "manifest": json.dumps(manifest)}
    resp = client.post("/api/v1/check/", data)
    assert resp.json() == {"status": "ok"}


@pytest.mark.parametrize(
    "downloaded_data,expected_status",
    [
        (
            (  # default download (as expected from a current `opensafely codelists update`)
                "code,term,dmd_id,dmd_type,bnf_code\r\n"
                "10514511000001106,Adrenaline (base) 220micrograms/dose inhaler,10514511000001106,VMP,0301012A0AAABAB\r\n"
                "10525011000001107,Adrenaline (base) 220micrograms/dose inhaler refill,10525011000001107,VMP,0301012A0AAACAC\r\n"
                "999,VMP previous to 10514511000001106,999,VMP,0301012A0AAABAB\r\n"
            ),
            "ok",
        ),
        (
            (  # download with code, term and original code column
                "code,term,dmd_id\r\n"
                "10514511000001106,Adrenaline (base) 220micrograms/dose inhaler,10514511000001106\r\n"
                "10525011000001107,Adrenaline (base) 220micrograms/dose inhaler refill,10525011000001107\r\n"
                "999,VMP previous to 10514511000001106,999\r\n"
            ),
            "ok",
        ),
        (
            (  # old-style download (from before VMPs were mapped into dmd downloads)
                "dmd_type,dmd_id,dmd_name,bnf_code\r\n"
                "VMP,10514511000001106,Adrenaline (base) 220micrograms/dose inhaler,0301012A0AAABAB\r\n"
                "VMP,10525011000001107,Adrenaline (base) 220micrograms/dose inhaler refill,0301012A0AAACAC\r\n"
            ),
            "error",
        ),
        (
            (  # download excluding original code column
                "code,term\r\n"
                "10514511000001106,Adrenaline (base) 220micrograms/dose inhaler\r\n"
                "10525011000001107,Adrenaline (base) 220micrograms/dose inhaler refill\r\n"
                "999,VMP previous to 10514511000001106\r\n"
            ),
            "ok",
        ),
    ],
)
def test_codelists_check_dmd_alternative_downloads_with_vmp_mappings(
    client, dmd_version_asthma_medication, downloaded_data, expected_status
):
    # Add a VMP mapping which will be added into the CSV download
    VmpPrevMapping.objects.create(id="10514511000001106", vpidprev="999")
    codelist_id = (
        f"{dmd_version_asthma_medication.organisation.slug}/"
        f"{dmd_version_asthma_medication.codelist.slug}/"
        f"{dmd_version_asthma_medication.hash}"
    )
    codelist_csv_id = codelist_id.replace("/", "-") + ".csv"

    manifest = {
        "files": {
            codelist_csv_id: {
                "id": codelist_id,
                "url": f"https://opencodelist.org/codelists/{codelist_csv_id}/",
                "downloaded_at": "2023-10-04 13:55:17.569997Z",
                "sha": dmd_version_asthma_medication.csv_data_sha(
                    csv_data=downloaded_data
                ),
            },
        }
    }
    data = {"codelists": codelist_id, "manifest": json.dumps(manifest)}
    resp = client.post("/api/v1/check/", data)
    assert resp.json()["status"] == expected_status


def test_codelists_check_sha(version_with_no_searches):
    # The CSV data download contains \r\n line endings
    assert version_with_no_searches.csv_data_for_download() == (
        "code,term\r\n"
        "128133004,Disorder of elbow\r\n"
        "156659008,(Epicondylitis &/or tennis elbow) or (golfers' elbow)\r\n"
        "239964003,Soft tissue lesion of elbow region\r\n"
        "35185008,Enthesopathy of elbow region\r\n"
        "429554009,Arthropathy of elbow\r\n"
        "73583000,Epicondylitis\r\n"
    )
    # In order to avoid different OS messing with line endings, opensafely-cli
    # splits the lines and rejoins them before hashing. Test that our
    # csv_data_sha does the same
    csv_data_clean = (
        "code,term\n"
        "128133004,Disorder of elbow\n"
        "156659008,(Epicondylitis &/or tennis elbow) or (golfers' elbow)\n"
        "239964003,Soft tissue lesion of elbow region\n"
        "35185008,Enthesopathy of elbow region\n"
        "429554009,Arthropathy of elbow\n"
        "73583000,Epicondylitis"
    )
    assert (
        version_with_no_searches.csv_data_sha()
        == hashlib.sha1(csv_data_clean.encode()).hexdigest()
    )


def test_codelists_check_non_downloadable_dmd(client, dmd_version_asthma_medication):
    dmd_version_asthma_medication.csv_data = (
        dmd_version_asthma_medication.csv_data.replace("dmd_id", "bad_header")
    )
    dmd_version_asthma_medication.save()

    assert not dmd_version_asthma_medication.downloadable

    codelist_id = (
        f"{dmd_version_asthma_medication.organisation.slug}/"
        f"{dmd_version_asthma_medication.codelist.slug}/"
        f"{dmd_version_asthma_medication.hash}"
    )
    codelist_csv_id = codelist_id.replace("/", "-") + ".csv"

    # Test the happy path for this dmd version
    manifest = {
        "files": {
            codelist_csv_id: {
                "id": codelist_id,
                "url": f"https://opencodelist.org/codelists/{codelist_csv_id}/",
                "downloaded_at": "2023-10-04 13:55:17.569997Z",
                "sha": "dummy-sha",
            },
        }
    }
    data = {"codelists": codelist_id, "manifest": json.dumps(manifest)}
    resp = client.post("/api/v1/check/", data)
    assert resp.json() == {
        "status": "error",
        "data": {"error": f"{codelist_id} is not downloadable"},
    }
