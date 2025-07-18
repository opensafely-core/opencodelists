from django.urls import reverse


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
