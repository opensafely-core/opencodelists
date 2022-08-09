from coding_systems.snomedct.coding_system import (
    code_to_term,
    codes_by_type,
    lookup_names,
)


def test_codes_by_type(snomedct_data):
    assert codes_by_type(
        ["705115006", "239964003", "106077005", "722135009"], None
    ) == {
        "Core Metadata Concept": ["705115006", "722135009"],
        "Disorder": ["239964003"],
        "Finding": ["106077005"],
    }


def test_lookup_names(snomedct_data):
    assert lookup_names(["705115006", "239964003", "99999"]) == {
        "239964003": "Soft tissue lesion of elbow region (disorder)",
        "705115006": "Technology Preview module (core metadata concept)",
    }


def test_code_to_term(snomedct_data):
    assert code_to_term(["705115006", "239964003", "99999"]) == {
        "239964003": "Soft tissue lesion of elbow region",
        "705115006": "Technology Preview module",
        "99999": "Unknown",
    }
