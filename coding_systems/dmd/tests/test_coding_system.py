from coding_systems.dmd.coding_system import code_to_term, lookup_names


def test_lookup_names(dmd_data):
    assert list(lookup_names(["10514511000001106", "10525011000001107", "99999"])) == [
        ("10514511000001106", "Adrenaline (base) 220micrograms/dose inhaler (VMP)"),
        (
            "10525011000001107",
            "Adrenaline (base) 220micrograms/dose inhaler refill (VMP)",
        ),
    ]


def test_code_to_term(dmd_data):
    assert code_to_term(["10514511000001106", "10525011000001107", "99999"]) == {
        "10514511000001106": "Adrenaline (base) 220micrograms/dose inhaler (VMP)",
        "10525011000001107": "Adrenaline (base) 220micrograms/dose inhaler refill (VMP)",
        "99999": "Unknown",
    }
