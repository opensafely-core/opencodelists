import pytest

from coding_systems.dmd.coding_system import CodingSystem


@pytest.fixture
def coding_system():
    yield CodingSystem(database_alias="dmd_test_20200101")


def test_lookup_names(dmd_data, coding_system):
    assert coding_system.lookup_names(
        ["10514511000001106", "10525011000001107", "99999"]
    ) == {
        "10514511000001106": "Adrenaline (base) 220micrograms/dose inhaler (VMP)",
        "10525011000001107": "Adrenaline (base) 220micrograms/dose inhaler refill (VMP)",
    }


def test_code_to_term(dmd_data, coding_system):
    assert coding_system.code_to_term(
        ["10514511000001106", "10525011000001107", "99999"]
    ) == {
        "10514511000001106": "Adrenaline (base) 220micrograms/dose inhaler (VMP)",
        "10525011000001107": "Adrenaline (base) 220micrograms/dose inhaler refill (VMP)",
        "99999": "Unknown",
    }


def test_ancestor_relationships(dmd_data, coding_system):
    """
    Test that given each of a code of type [AMP, VMP, VTM]
    the ancestor relationships all the way up to the ultimate
    ancestor VTM(s) are returned
    """

    # "Salbutamol" VTM has no ancestors
    salbutamol_vtm = "777483005"
    expected_relationships = set()

    assert (
        coding_system.ancestor_relationships([salbutamol_vtm]) == expected_relationships
    )

    # 35936411000001109:"Salbutamol 100micrograms/dose breath actuated inhaler"
    # and 39112711000001103:"Salbutamol 100micrograms/dose breath actuated inhaler CFC free"
    # share a common ancestor of 777483005:"Salbutamol"

    salbutamol_vmps = ["35936411000001109", "39112711000001103"]
    expected_relationships |= {(salbutamol_vtm, vmp) for vmp in salbutamol_vmps}

    assert (
        coding_system.ancestor_relationships(salbutamol_vmps) == expected_relationships
    )

    # "Adrenaline" VTM has no ancestors
    adrenaline_vtm = "65502005"

    # "Adrenaline (base) 220micrograms/dose inhaler" has an ancestor of "Adrenaline" VTM
    # and no relation to Salbutamol
    adrenaline_vmps = ["10514511000001106"]

    assert coding_system.ancestor_relationships(salbutamol_vmps + adrenaline_vmps) == (
        expected_relationships | {(adrenaline_vtm, vmp) for vmp in adrenaline_vmps}
    )

    # 3293111000001105:"Aerolin 100micrograms/dose Autohaler" has an ancestor of VMP 35936411000001109
    # and, in turn, VTM 777483005
    salbutamol_amps = ["3293111000001105"]
    expected_relationships |= {("35936411000001109", "3293111000001105")}
    assert (
        coding_system.ancestor_relationships(salbutamol_vmps + salbutamol_amps)
        == expected_relationships
    )

    # 3436211000001104: "Oxygen composite cylinders 1360litres B10C with integral headset" has no VTM
    # and three descendant AMPS: 4086311000001109,4086111000001107,3106411000001109
    oxygen_vmp = "3436211000001104"
    oxygen_amps = ["4086311000001109", "4086111000001107", "3106411000001109"]
    expected_relationships = {(oxygen_vmp, amp) for amp in oxygen_amps}
    assert coding_system.ancestor_relationships(oxygen_amps) == expected_relationships


def test_descendant_relationships(dmd_data, coding_system):
    """
    Test that given each of a code of type [AMP, VMP, VTM]
    the descendant relationships all the way down to the ultimate
    descendant AMP(s) are returned
    """

    # A section of the AMP-VMP-VTM hierarchy for Salbutamol
    salbutamol_amps = ["597011000001101", "18148111000001107", "22503111000001109"]
    salbutamol_vmp = "39113611000001102"
    salbutamol_vtm = "777483005"

    # AMPs have no descendants
    expected_relationships = set()
    assert (
        coding_system.descendant_relationships(salbutamol_amps)
        == expected_relationships
    )

    # Given VMP has three descendant AMPs
    expected_relationships |= {(salbutamol_vmp, amp) for amp in salbutamol_amps}
    assert (
        coding_system.descendant_relationships([salbutamol_vmp])
        == expected_relationships
    )

    # Given VTM has 10 descendant VMPs, which have in total 10 descendant AMPs
    expected_relationships |= {(salbutamol_vtm, salbutamol_vmp)}
    descendant_relationships = coding_system.descendant_relationships([salbutamol_vtm])

    assert expected_relationships.issubset(descendant_relationships)

    # 10 VTM-VMP relationships + 10 VMP-AMP == 20
    # minus the four we have manually declared above
    assert len(descendant_relationships - expected_relationships) == 16

    # 3436211000001104: "Oxygen composite cylinders 1360litres B10C with integral headset" has no VTM
    # and three descendant AMPS: 4086311000001109,4086111000001107,3106411000001109
    oxygen_vmp = "3436211000001104"
    oxygen_amps = ["4086311000001109", "4086111000001107", "3106411000001109"]
    expected_relationships = {(oxygen_vmp, amp) for amp in oxygen_amps}
    assert (
        coding_system.descendant_relationships([oxygen_vmp]) == expected_relationships
    )


def test_codes_by_type(dmd_data, coding_system):
    # Ing, VTM, VMP, AMP
    salbutamol_codes = [
        "372897005",
        "777483005",
        "35936411000001109",
        "3293111000001105",
    ]

    assert coding_system.codes_by_type(salbutamol_codes, None) == {
        "Product": salbutamol_codes,
    }

    unknown_codes = ["1234567890"]

    assert coding_system.codes_by_type(salbutamol_codes + unknown_codes, None) == {
        "Product": salbutamol_codes,
        "[unknown]": unknown_codes,
    }


def test_search_by_term(dmd_data, coding_system):
    term = "salbutamol"
    vmps_containing_term = {
        "35936411000001109",  # Salbutamol 100micrograms/dose breath actuated inhaler
        "39112711000001103",  # Salbutamol 100micrograms/dose breath actuated inhaler CFC free
        "13566111000001109",  # Salbutamol 100micrograms/dose dry powder inhalation cartridge
        "13566211000001103",  # Salbutamol 100micrograms/dose dry powder inhalation cartridge with device
        "9207411000001106",  # Salbutamol 100micrograms/dose dry powder inhaler
        "35936511000001108",  # Salbutamol 100micrograms/dose inhaler
        "39113611000001102",  # Salbutamol 100micrograms/dose inhaler CFC free
        "43207011000001101",  # Salbutamol 2.5mg/2.5ml nebuliser liquid unit dose ampoules
        "39709611000001109",  # Salbutamol 2.5mg/2.5ml nebuliser liquid unit dose vials
        "42718411000001106",  # Salbutamol 2.5mg/3ml nebuliser liquid unit dose vials
    }
    amps_containing_term = {
        "38131211000001109",  # Easyhaler Salbutamol sulfate 100micrograms/dose dry powder inhaler
        "9205211000001104",  # Easyhaler Salbutamol sulfate 100micrograms/dose dry powder inhaler
    }
    vtms_containing_term = {"777483005"}  # Salbutamol
    assert (
        coding_system.search_by_term(term)
        == vmps_containing_term | amps_containing_term | vtms_containing_term
    )

    # Test that an ingredient like "codeine" matches the VTM and VMPs "co-codamol"
    term = "codeine"
    expected_response = {
        "44102411000001107",  # VTM: Co-codamol
        "44159611000001106",  # VMP: Co-codamol 30mg/500mg effervescent tablets sugar free
        "38555211000001104",  # VMP: Co-codamol 8mg/500mg effervescent tablets sugar free
    }

    assert coding_system.search_by_term(term) == expected_response


@pytest.mark.parametrize(
    "term, expected_response",
    [
        ("TEST_STRING_for_AMP_abbreviation", {"4086111000001107"}),
        ("TEST_STRING_for_AMP_description", {"4086111000001107"}),
        ("TEST_STRING_for_AMP_previous_name", {"4086111000001107"}),
        ("TEST_STRING_for_VMP_abbreviation", {"38555211000001104"}),
        ("TEST_STRING_for_VMP_previous_name", {"38555211000001104"}),
        ("TEST_STRING_for_VTM_abbreviation", {"44102411000001107"}),
    ],
)
def test_search_by_term_specific_fields(
    dmd_data, coding_system, term, expected_response
):
    assert coding_system.search_by_term(term) == expected_response


@pytest.mark.parametrize(
    "code, expected_response",
    [
        ("597011000001101", {"597011000001101"}),  # AMP code
        ("35936411000001109", {"35936411000001109"}),  # VMP code
        ("777483005", {"777483005"}),  # VTM code
        (
            "372897005",
            {"35936511000001108", "777483005", "9207411000001106"},
        ),  # Ing code
        ("111", set()),  # Unknown code returns empty set
    ],
)
def test_search_by_code(dmd_data, coding_system, code, expected_response):
    assert coding_system.search_by_code(code) == expected_response
