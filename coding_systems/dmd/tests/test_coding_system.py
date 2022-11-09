import pytest

from coding_systems.dmd.coding_system import CodingSystem


@pytest.fixture
def coding_system():
    yield CodingSystem(database_alias="dmd_test_20200101")


def test_lookup_names(dmd_data, coding_system):
    assert list(
        coding_system.lookup_names(["10514511000001106", "10525011000001107", "99999"])
    ) == [
        ("10514511000001106", "Adrenaline (base) 220micrograms/dose inhaler (VMP)"),
        (
            "10525011000001107",
            "Adrenaline (base) 220micrograms/dose inhaler refill (VMP)",
        ),
    ]


def test_code_to_term(dmd_data, coding_system):
    assert coding_system.code_to_term(
        ["10514511000001106", "10525011000001107", "99999"]
    ) == {
        "10514511000001106": "Adrenaline (base) 220micrograms/dose inhaler (VMP)",
        "10525011000001107": "Adrenaline (base) 220micrograms/dose inhaler refill (VMP)",
        "99999": "Unknown",
    }
