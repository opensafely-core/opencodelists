import pytest

from coding_systems.icd10.claml_parser import ICD10Code, ModifierDigit
from coding_systems.icd10.known_diffs import (
    RubricChange,
    TermDifference,
    clinically_different_codes,
    codes_with_different_descriptions,
    expand_who_2016_place_of_occurrence,
    get_2016_2019_description_difference,
    is_2016_claml_only,
    is_2016_description_difference,
    is_2016_scraped_only,
    moved_codes,
    should_include_2016_claml_only,
    should_include_2016_scraped_only,
    should_use_scraped_for_2016,
)


def test_term_difference_rejects_unknown_source_choice():
    with pytest.raises(ValueError, match="use must be 'claml' or 'scraped'"):
        TermDifference(claml="A", scraped="B", use="neither")


def test_rubric_change_defaults_to_who_rubrics():
    change = RubricChange(
        who={"inclusion": ["A"]},
    )

    assert change.resolved_use == {"inclusion": ["A"]}


def test_rubric_change_derives_use_from_edits_without_mutating_who():
    who = {
        "inclusion": ["A", "B"],
        "exclusion": ["old value", "remove me"],
    }
    change = RubricChange(
        who=who,
        replace={"exclusion": {"old": "new"}},
        remove={"exclusion": ["remove me"]},
        add={"note": ["C"]},
    )

    assert change.resolved_use == {
        "inclusion": ["A", "B"],
        "exclusion": ["new value"],
        "note": ["C"],
    }
    assert who == {
        "inclusion": ["A", "B"],
        "exclusion": ["old value", "remove me"],
    }


def test_rubric_change_adds():
    change = RubricChange(
        who={"inclusion": ["A"]},
        add={"inclusion": ["B"], "exclusion": ["C"]},
    )

    assert change.resolved_use == {"inclusion": ["A", "B"], "exclusion": ["C"]}


def test_rubric_change_removes():
    change = RubricChange(
        who={"inclusion": ["A", "B"], "exclusion": ["C"]},
        remove={"inclusion": ["B"], "exclusion": ["C"]},
    )

    assert change.resolved_use == {"inclusion": ["A"]}


def test_rubric_change_replaces_substrings_in_each_rubric_value():
    change = RubricChange(
        who={
            "inclusion": [
                "Angiostrongyliasis due to: Angiostrongylus costaricensis (B83.2)"
            ],
            "exclusion": [
                "Angiostrongyliasis due to: Angiostrongylus costaricensis (B83.2)",
                "Angiostrongyliasis due to: Parastrongylus costaricensis (B83.2)",
            ],
        },
        replace={"exclusion": {"costaricensis": "cantonensis"}},
    )

    assert change.resolved_use == {
        "inclusion": [
            "Angiostrongyliasis due to: Angiostrongylus costaricensis (B83.2)"
        ],
        "exclusion": [
            "Angiostrongyliasis due to: Angiostrongylus cantonensis (B83.2)",
            "Angiostrongyliasis due to: Parastrongylus cantonensis (B83.2)",
        ],
    }


def test_2016_claml_vs_scraped_known_difference_helpers():
    assert is_2016_claml_only("M1400")
    assert not is_2016_scraped_only("M1400")
    assert should_include_2016_claml_only("M1400") is True
    assert should_include_2016_scraped_only("M1400") is False

    assert is_2016_description_difference(
        "J10",
        "influenza due to identified seasonal influenza virus",
        "Influenza due to identified seasonal influenza virus",
    )
    assert not is_2016_description_difference(
        "J10",
        "wrong",
        "Influenza due to identified seasonal influenza virus",
    )
    assert should_use_scraped_for_2016("J10") is True
    assert should_use_scraped_for_2016("U06") is False


def test_2016_vs_2019_known_difference_helpers_classify_clinical_significance():
    equivalent = get_2016_2019_description_difference(
        "A081",
        "Acute gastroenteropathy due to Norwalk agent",
        "Acute gastroenteropathy due to Norovirus",
    )
    different = get_2016_2019_description_difference(
        "W260",
        "Contact with other sharp object(s) (Home)",
        "Contact with knife, sword or dagger",
    )

    assert equivalent is not None
    assert equivalent.clinically_equivalent is True
    assert different is not None
    assert different.clinically_equivalent is False

    assert (
        get_2016_2019_description_difference(
            "WRONG",
            "Acute gastroenteropathy due to Norwalk agent",
            "Acute gastroenteropathy due to Norovirus",
        )
        is None
    )

    assert (
        get_2016_2019_description_difference(
            "A081",
            "Acute gastroenteropathy due to Norwalk agent",
            "wrong",
        )
        is None
    )


def test_expand_who_2016_place_of_occurrence_applies_range_and_exceptions(
    monkeypatch,
):
    records = {
        "V99": ICD10Code(code="V99", parent=None, description="Transport accident"),
        "W00": ICD10Code(code="W00", parent=None, description="Fall"),
        "W26": ICD10Code(code="W26", parent=None, description="Sharp object"),
        "W260": ICD10Code(code="W260", parent="W26", description="WHO W26 child"),
        "X34": ICD10Code(code="X34", parent=None, description="Earthquake"),
        "X340": ICD10Code(code="X340", parent="X34", description="WHO X34 child"),
        "X59": ICD10Code(code="X59", parent=None, description="Unspecified factor"),
        "X590": ICD10Code(code="X590", parent="X59", description="WHO X59 child"),
        "Y06": ICD10Code(code="Y06", parent=None, description="Neglect"),
        "Y34": ICD10Code(code="Y34", parent=None, description="Undetermined event"),
        "Y35": ICD10Code(code="Y35", parent=None, description="Legal intervention"),
    }
    modifiers = [ModifierDigit(digit_code="0", description="Home")]
    monkeypatch.setattr(
        "coding_systems.icd10.known_diffs.WHO_2016_EXPECTED_OVERRIDES",
        frozenset({"W260", "X340", "X590"}),
    )

    place_records = expand_who_2016_place_of_occurrence(records, modifiers)

    assert set(place_records) == {"W000", "W260", "X340", "X590", "Y340"}
    assert place_records["W000"].parent == "W00"
    assert place_records["W000"].term_modifier == "Home"
    assert "Y060" not in place_records
    assert "Y350" not in place_records


def test_expand_who_2016_place_of_occurrence_fails_on_unexpected_overlap(
    monkeypatch,
):
    records = {
        "W00": ICD10Code(code="W00", parent=None, description="Fall"),
        "W000": ICD10Code(code="W000", parent="W00", description="Existing child"),
    }
    modifiers = [ModifierDigit(digit_code="0", description="Home")]
    monkeypatch.setattr(
        "coding_systems.icd10.known_diffs.WHO_2016_EXPECTED_OVERRIDES",
        frozenset(),
    )

    with pytest.raises(AssertionError, match="overlap with unexpected existing codes"):
        expand_who_2016_place_of_occurrence(records, modifiers)


def test_expand_who_2016_place_of_occurrence_fails_when_expected_override_missing(
    monkeypatch,
):
    records = {"W00": ICD10Code(code="W00", parent=None, description="Fall")}
    modifiers = [ModifierDigit(digit_code="0", description="Home")]
    monkeypatch.setattr(
        "coding_systems.icd10.known_diffs.WHO_2016_EXPECTED_OVERRIDES",
        frozenset({"X590"}),
    )

    with pytest.raises(AssertionError, match="expected codes missing"):
        expand_who_2016_place_of_occurrence(records, modifiers)


def test_clinically_different_codes():
    differences = clinically_different_codes(["w260", "W260", "A081", "ZZZZ"])

    # Should deduplicate w260/W260 and only return the clinically different
    # code W260, not A081 which is clinically equivalent, or ZZZZ which is
    # not a known difference.
    assert differences == {
        "W260": {
            "combined_2016": "Contact with other sharp object(s) (Home)",
            "who_2019": "Contact with knife, sword or dagger",
        }
    }


def test_moved_codes():
    possible_codes = moved_codes(
        ["U09", "U099", "U11", "U11", "K583", "K588", "K589", "ZZZZ"]
    )

    assert possible_codes == [
        {
            "title": "Irritable bowel syndrome",
            "nhs2016": ["K58", "K580", "K589"],
            "who2019": ["K58", "K581", "K582", "K583", "K588"],
            "comment": "The codes for this were K580 and K589 in 2016, but K581, K582, K583 and K588 in 2019. You likely want all these codes in your codelist. However if you are specifically looking for diarrhoea, or constipation, rather than IBS, then you may only want some but not all of these codes.",
        },
        {
            "title": "Post COVID-19 condition",
            "nhs2016": ["U074"],
            "who2019": ["U09", "U099"],
            "comment": "This is U074 in 2016, but U09/U099 in 2019.",
        },
        {
            "title": "Need for immunization against COVID-19",
            "nhs2016": ["U076"],
            "who2019": ["U11", "U119"],
            "comment": "This is U076 in 2016, but U11/U119 in 2019.",
        },
    ]


def test_codes_with_different_descriptions():
    codes = ["P710", "P710", "P711", "ZZZZ", "X590"]
    differences = codes_with_different_descriptions(codes)

    assert differences == {
        "P710": {
            "combined_2016": "Cow's milk hypocalcaemia in newborn",
            "who_2019": "Cow milk hypocalcaemia in newborn",
            "equivalent": True,
        },
        "X590": {
            "combined_2016": "Exposure to unspecified factor (Home)",
            "who_2019": "Exposure to unspecified factor causing fracture",
            "equivalent": False,
        },
    }
