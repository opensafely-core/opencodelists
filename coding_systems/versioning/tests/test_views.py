from django.urls import reverse

from coding_systems.icd10.models import ConceptRubric, RubricKind


def test_latest_releases(client, setup_coding_systems):
    response = client.get(reverse("versioning:latest_releases"))
    from codelists.coding_systems import CODING_SYSTEMS

    assert response.status_code == 200
    # Coding system releases with database aliases (i.e. not "null", "opcs4", "readv2", "experiment")
    # are shown
    latest_releases_ids = {
        release.id for release in response.context["latest_releases"]
    }
    assert latest_releases_ids == {"icd10", "snomedct", "ctv3", "dmd", "bnf"}
    assert set(CODING_SYSTEMS) - latest_releases_ids == {
        "null",
        "opcs4",
        "readv2",
        "experiment",
    }


def test_latest_releases_json_without_pcd_refset(client, setup_coding_systems):
    response = client.get(
        reverse("versioning:latest_releases"),
        {"type": "json"},
        HTTP_ACCEPT="application/json",
    )
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {
        "icd10",
        "snomedct",
        "ctv3",
        "dmd",
        "bnf",
    }


def test_latest_releases_json_with_pcd_refset(
    client, setup_coding_systems, pcd_refset_version, nhs_drug_refset_version
):
    response = client.get(
        reverse("versioning:latest_releases"),
        {"type": "json"},
        HTTP_ACCEPT="application/json",
    )
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {
        "icd10",
        "snomedct",
        "ctv3",
        "dmd",
        "bnf",
        "pcd_refsets",
        "nhs_drug_refsets",
    }
    assert data["pcd_refsets"]["release"] == pcd_refset_version.release
    assert data["nhs_drug_refsets"]["release"] == nhs_drug_refset_version.release


def test_more_info_returns_additional_rubrics(client, setup_coding_systems, icd10_data):
    ConceptRubric.objects.using("icd10_test_20200101").create(
        concept_edition_id=13,
        kind=RubricKind.INCLUSION,
        text="Golfer's elbow",
    )

    response = client.post(
        "/coding-systems/more-info/icd10",
        {"codes": ["M770"]},
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.json() == {
        "synonyms": {},
        "references": {},
        "rubrics": {
            "M770": {
                "concept_rubrics": {RubricKind.INCLUSION: ["Golfer's elbow"]},
                "modifier_rubrics": {},
            }
        },
    }
