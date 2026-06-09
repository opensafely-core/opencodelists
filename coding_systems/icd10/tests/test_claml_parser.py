from pathlib import Path

from coding_systems.icd10.claml_parser import (
    ICD10Code,
    parse_claml,
)


# Stripped down version of the real claml file to test specific parts of claml_parser.py
# created by copying whole sections from the real file, and commenting out bits that
# would make it break (e.g. if a parent lists 5 children the parser complains if it
# doesn't find all of them)
CLAML_FIXTURE = (
    Path(__file__).parent.parent / "fixtures" / "claml" / "parser_examples.xml"
)


def test_parse_claml_handles_the_hierarchy():
    records, _ = parse_claml(CLAML_FIXTURE)

    # C403 > C40 > C40-C41 > C00-C75 > C00-C97 > II > root

    assert records["C403"] == ICD10Code(
        code="C403",
        parent="C40",
        description="Short bones of lower limb",
        description_long="Malignant neoplasm: Short bones of lower limb",
    )
    assert records["C40"] == ICD10Code(
        code="C40",
        parent="C40-C41",
        description="Malignant neoplasm of bone and articular cartilage of limbs",
    )
    assert records["C40-C41"] == ICD10Code(
        code="C40-C41",
        parent="C00-C75",
        description="Malignant neoplasms of bone and articular cartilage",
        concept_rubrics={
            "exclusion": [
                "bone marrow NOS (C96.7)",
                "synovia (C49.-)",
            ]
        },
    )
    assert records["C00-C75"] == ICD10Code(
        code="C00-C75",
        parent="C00-C97",
        description="Malignant neoplasms, stated or presumed to be primary, of specified sites, except of lymphoid, haematopoietic and related tissue",
    )
    assert records["C00-C97"].code == "C00-C97"
    assert records["C00-C97"].parent == "II"
    assert records["C00-C97"].description == "Malignant neoplasms"

    assert records["II"].code == "II"
    assert records["II"].parent is None
    assert records["II"].description == "Neoplasms"


def test_parse_claml_excludes_reference_text_from_description_but_keeps_usage_pair():
    records, _ = parse_claml(CLAML_FIXTURE)

    assert records["A170"].description == "Tuberculous meningitis"
    assert records["A170"].usage == "dagger"
    assert records["A170"].usage_pair_codes == [
        "G01",
    ]


def test_parse_claml_keeps_usage_pair_from_modifier_classes():
    records, _ = parse_claml(CLAML_FIXTURE)

    assert records["E102"].usage == "dagger"
    assert records["E102"].usage_pair_codes == ["N083", "N083", "N083"]


def test_parse_claml_separates_concept_and_modifier_rubrics():
    records, _ = parse_claml(CLAML_FIXTURE)

    assert records["C40-C41"].concept_rubrics == {
        "exclusion": [
            "bone marrow NOS (C96.7)",
            "synovia (C49.-)",
        ]
    }
    assert records["C40-C41"].modifier_rubrics == {}

    assert records["E100"].concept_rubrics == {}
    assert records["E100"].modifier_rubrics == {
        "inclusion": [
            "Diabetic: coma with or without ketoacidosis",
            "Diabetic: hyperosmolar coma",
            "Diabetic: hypoglycaemic coma",
            "Hyperglycaemic coma NOS",
        ]
    }


def test_parse_claml_handles_subscripts_in_descriptions():
    records, _ = parse_claml(CLAML_FIXTURE)

    assert records["D51"].description == "Vitamin B12 deficiency anaemia"


# Pattern A from claml_parser.py: 4th character modifiers to a 3 character code that
# has no 4-character children. The 3-char code is expanded to new 4-character codes
def test_parse_claml_expands_dotted_fourth_character_modifier():
    records, _ = parse_claml(CLAML_FIXTURE)

    assert records["E100"] == ICD10Code(
        code="E100",
        parent="E10",
        description="Type 1 diabetes mellitus",
        term_modifier="With coma",
        modifier_position=4,
        modifier_rubrics={
            "inclusion": [
                "Diabetic: coma with or without ketoacidosis",
                "Diabetic: hyperosmolar coma",
                "Diabetic: hypoglycaemic coma",
                "Hyperglycaemic coma NOS",
            ]
        },
    )


# Pattern B from claml_parser.py: 4th character modifiers to a 3 character codes that
# has 4 character children. The 4-char children are expanded to new 5-character codes
def test_parse_claml_expands_fourth_character_modifier_with_four_character_children():
    records, _ = parse_claml(CLAML_FIXTURE)

    assert records["I7000"] == ICD10Code(
        code="I7000",
        parent="I700",
        description="Atherosclerosis of aorta",
        term_modifier="without gangrene",
        modifier_position=4,
    )


# Pattern C from claml_parser.py: 5th character modifiers to a 3 character code that
# has no 4-character children. The 3-char code is  expanded to new 5-character codes with an X
def test_parse_claml_expands_fifth_character_modifier_with_no_four_character_children():
    records, _ = parse_claml(CLAML_FIXTURE)

    assert records["M45X0"] == ICD10Code(
        code="M45X0",
        parent="M45",
        description="Ankylosing spondylitis",
        term_modifier="Multiple sites in spine",
        modifier_position=5,
    )


# Pattern D from claml_parser.py: 5th character modifiers to a 3 character code that
# has 4-character children. The 4-char children are expanded to new 5-character codes
def test_parse_claml_expands_fifth_character_modifier_with_four_character_children():
    records, _ = parse_claml(CLAML_FIXTURE)

    assert records["M0000"] == ICD10Code(
        code="M0000",
        parent="M000",
        description="Staphylococcal arthritis and polyarthritis",
        term_modifier="Multiple sites",
        modifier_position=5,
    )


# Pattern E from claml_parser.py: 5th character modifiers on a 4 character code. The
# 4-char code is expanded to new 5-character codes
def test_parse_claml_expands_fifth_character_modifier_on_four_character_base():
    records, _ = parse_claml(CLAML_FIXTURE)

    assert records["T1420"] == ICD10Code(
        code="T1420",
        parent="T142",
        description="Fracture of unspecified body region",
        term_modifier="closed",
        modifier_position=5,
    )


def test_parse_claml_expands_expected_implicit_modifiedby():
    records, _ = parse_claml(CLAML_FIXTURE)

    assert records["M1300"] == ICD10Code(
        code="M1300",
        parent="M130",
        description="Polyarthritis, unspecified",
        term_modifier="Multiple sites",
        modifier_position=5,
    )


def test_term_returns_long_description_if_available():
    records, _ = parse_claml(CLAML_FIXTURE)

    # C403 has a long description, so term should return that
    assert records["C403"].term == records["C403"].description_long
    assert records["C403"].term != records["C403"].description
    # A170 has no long description, so term should return the short description
    assert records["A170"].term == records["A170"].description
    assert records["A170"].term != records["A170"].description_long


def test_term_with_modifier():
    records, _ = parse_claml(CLAML_FIXTURE)

    # M1300 has a term_modifier, so term_with_modifier should return the description + modifier
    assert (
        records["M1300"].term_with_modifier
        == "Polyarthritis, unspecified (Multiple sites)"
    )
    # C403 has no term_modifier, so term_with_modifier should return the description
    assert records["C403"].term_with_modifier == records["C403"].term


def test_short_term_with_modifier():
    records, _ = parse_claml(CLAML_FIXTURE)

    # M1300 has a term_modifier, so short_term_with_modifier should return the description + modifier
    assert (
        records["M1300"].short_term_with_modifier
        == "Polyarthritis, unspecified (Multiple sites)"
    )
    # C403 has no term_modifier, so short_term_with_modifier should return the description
    assert records["C403"].short_term_with_modifier == records["C403"].description


def test_raise_error_if_no_label_in_rubric():
    from xml.etree import ElementTree as ET

    from coding_systems.icd10.claml_parser import _get_label_text

    rubric_xml = """
    <Rubric>
        <Meta name="usage" value="optional"/>
    </Rubric>
    """
    rubric_element = ET.fromstring(rubric_xml)

    try:
        _get_label_text(rubric_element)
        assert False, (
            "Expected ValueError to be raised when no Label element is found in Rubric"
        )
    except ValueError as e:
        assert (
            str(e)
            == f"Expected Rubric element to contain a Label child, but none found in {ET.tostring(rubric_element)}"
        )


def test_raise_error_if_no_reference_in_modifierlink_rubric():
    from xml.etree import ElementTree as ET

    from coding_systems.icd10.claml_parser import _find_implicit_modifiedby

    claml_xml = """
    <ClaML>
    <Class code="A17">
        <Rubric kind="modifierlink">
            <Label>
                <!-- Missing Reference element here -->
            </Label>
        </Rubric>
    </Class>
    </ClaML>
    """
    claml_element = ET.fromstring(claml_xml)
    try:
        _find_implicit_modifiedby(claml_element)
        assert False, (
            "Expected ValueError to be raised when no Reference element is found in modifierlink Rubric"
        )
    except ValueError as e:
        assert (
            str(e)
            == "Expected to find a Reference inside modifierlink Rubric for Class A17, but none found"
        )


def test_raise_error_if_no_code_in_modifierlink_rubric():
    from xml.etree import ElementTree as ET

    from coding_systems.icd10.claml_parser import _find_implicit_modifiedby

    claml_xml = """
    <ClaML>
    <Class code="A17">
        <Rubric kind="modifierlink">
            <Label>
                <Reference/> <!-- Missing code attribute here -->
            </Label>
        </Rubric>
    </Class>
    </ClaML>
    """
    claml_element = ET.fromstring(claml_xml)
    try:
        _find_implicit_modifiedby(claml_element)
        assert False, (
            "Expected ValueError to be raised when no code attribute is found in Reference element of modifierlink Rubric"
        )
    except ValueError as e:
        assert (
            str(e)
            == "Expected to find a Reference inside modifierlink Rubric for Class A17, but none found"
        )


def test_parse_claml_returns_place_modifier_digits():
    _, place_modifiers = parse_claml(CLAML_FIXTURE)

    assert [(m.digit_code, m.description) for m in place_modifiers] == [
        ("0", "Home"),
        ("1", "Residential institution"),
        ("2", "School, other institution and public administrative area"),
        ("3", "Sports and athletics area"),
        ("4", "Street and highway"),
        ("5", "Trade and service area"),
        ("6", "Industrial and construction area"),
        ("7", "Farm"),
        ("8", "Other specified places"),
        ("9", "Unspecified place"),
    ]
    assert place_modifiers[0].rubrics["inclusion"] == [
        "Apartment",
        "Boarding-house",
        "Caravan [trailer] park, residential",
        "Farmhouse",
        "Home premises",
        "House (residential)",
        "Noninstitutional place of residence",
        "Private: driveway to home",
        "Private: garage",
        "Private: garden to home",
        "Private: yard to home",
        "Swimming-pool in private house or garden",
    ]
