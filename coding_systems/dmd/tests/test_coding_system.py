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
