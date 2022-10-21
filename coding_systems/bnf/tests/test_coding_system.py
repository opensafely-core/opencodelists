import pytest

from coding_systems.bnf.coding_system import CodingSystem
from coding_systems.bnf.models import Concept


@pytest.fixture
def coding_system():
    yield CodingSystem(database_alias="bnf_test_20200101")


def test_lookup_names(coding_system):
    for code in ["11111", "22222"]:
        Concept.objects.using("bnf_test_20200101").create(
            code=code[:2], type="Chapter", name=f"Chapter {code[:2]}"
        )
        Concept.objects.using("bnf_test_20200101").create(
            code=code, type="Section", name=f"Section {code}"
        )

    assert coding_system.lookup_names(["11111", "22222", "99999"]) == {
        "11111": "Section 11111",
        "22222": "Section 22222",
    }


def test_code_to_term(coding_system):
    for code in ["11111", "22222"]:
        Concept.objects.using("bnf_test_20200101").create(
            code=code[:2], type="Chapter", name=f"Chapter {code[:2]}"
        )
        Concept.objects.using("bnf_test_20200101").create(
            code=code, type="Section", name=f"Section {code}"
        )

    assert coding_system.code_to_term(["11111", "22222", "99999"]) == {
        "11111": "Section 11111",
        "22222": "Section 22222",
        "99999": "Unknown",
    }
