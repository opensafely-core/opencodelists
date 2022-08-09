from coding_systems.bnf.coding_system import code_to_term, lookup_names
from coding_systems.bnf.models import Concept


def test_lookup_names():
    for code in ["11111", "22222"]:
        Concept.objects.create(
            code=code[:2], type="Chapter", name=f"Chapter {code[:2]}"
        )
        Concept.objects.create(code=code, type="Section", name=f"Section {code}")

    assert lookup_names(["11111", "22222", "99999"]) == {
        "11111": "Section 11111",
        "22222": "Section 22222",
    }


def test_code_to_term():
    for code in ["11111", "22222"]:
        Concept.objects.create(
            code=code[:2], type="Chapter", name=f"Chapter {code[:2]}"
        )
        Concept.objects.create(code=code, type="Section", name=f"Section {code}")

    assert code_to_term(["11111", "22222", "99999"]) == {
        "11111": "Section 11111",
        "22222": "Section 22222",
        "99999": "Unknown",
    }
