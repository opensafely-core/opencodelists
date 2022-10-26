import pytest

from coding_systems.snomedct.coding_system import CodingSystem


@pytest.fixture
def coding_system():
    yield CodingSystem(database_alias="snomedct_test_20200101")


def test_codes_by_type(snomedct_data, coding_system):
    assert coding_system.codes_by_type(
        ["705115006", "239964003", "106077005", "722135009", "99999"], None
    ) == {
        "Core Metadata Concept": ["705115006", "722135009"],
        "Disorder": ["239964003"],
        "Finding": ["106077005"],
        "[unknown]": ["99999"],
    }


def test_lookup_names(snomedct_data, coding_system):
    assert coding_system.lookup_names(["705115006", "239964003", "99999"]) == {
        "239964003": "Soft tissue lesion of elbow region (disorder)",
        "705115006": "Technology Preview module (core metadata concept)",
    }


def test_code_to_term(snomedct_data, coding_system):
    assert coding_system.code_to_term(["705115006", "239964003", "99999"]) == {
        "239964003": "Soft tissue lesion of elbow region",
        "705115006": "Technology Preview module",
        "99999": "Unknown",
    }
