import pytest

from coding_systems.icd10.coding_system import CodingSystem


@pytest.fixture
def coding_system():
    yield CodingSystem(database_alias="icd10_test_20200101")


def test_codes_by_type(icd10_data, coding_system):
    assert coding_system.codes_by_type(
        ["A771", "XIII", "M60-M79", "M70-M79", "M77", "M770", "M779"], None
    ) == {
        "I: Certain infectious and parasitic diseases": ["A771"],
        "XIII: Diseases of the musculoskeletal system and connective tissue": [
            "XIII",
            "M60-M79",
            "M70-M79",
            "M77",
            "M770",
            "M779",
        ],
    }


def test_lookup_names(icd10_data, coding_system):
    assert coding_system.lookup_names(["M77", "M770", "99999"]) == {
        "M77": "Other enthesopathies",
        "M770": "Medial epicondylitis",
    }


def test_code_to_term(icd10_data, coding_system):
    assert coding_system.code_to_term(["M77", "M770", "99999"]) == {
        "M77": "Other enthesopathies",
        "M770": "Medial epicondylitis",
        "99999": "Unknown",
    }
