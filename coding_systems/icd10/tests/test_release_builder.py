import zipfile

import pytest
import structlog

from coding_systems.icd10.claml_parser import ICD10Code, ModifierDigit
from coding_systems.icd10.known_diffs import RubricChange
from coding_systems.icd10.release_builder import (
    apply_nhs_2016_alterations,
    build_2016_2019_diff_report,
    build_2016_claml_scraped_diff_report,
    check_diff_2016_claml_with_scraped,
    check_diff_2016_with_2019,
    combine_2016_claml_and_scraped_records,
    load_import_records,
)


def flatten_logs(captured_logs):
    return "".join([log["event"] for log in captured_logs if "event" in log])


@pytest.fixture(autouse=True)
def dummy_zip(tmp_path):
    zip_path = tmp_path / "icd10_combined.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("icd102016en.xml", "dummy 2016 content")
        zf.writestr("icd102019en.xml", "dummy 2019 content")
        zf.writestr("icd10nhs2016en.xml", "dummy NHS 2016 content")

    file_metadata = {
        "WHO_2019": {"xml_filename": "icd102019en.xml"},
        "WHO_2016": {"xml_filename": "icd102016en.xml"},
        "NHS_2016": {"xml_filename": "icd10nhs2016en.xml"},
    }
    return zip_path, file_metadata


def test_apply_nhs_2016_alterations_adds_place_codes(monkeypatch):
    records = {
        "W00": ICD10Code(code="W00", parent=None, description="Fall on same level"),
        "W26": ICD10Code(
            code="W26", parent=None, description="Contact with sharp objects"
        ),
        "W260": ICD10Code(
            code="W260", parent="W26", description="Literal WHO subcategory"
        ),
        "Y06": ICD10Code(code="Y06", parent=None, description="Neglect"),
    }
    place_modifiers = [ModifierDigit(digit_code="0", description="Home")]

    monkeypatch.setattr(
        "coding_systems.icd10.known_diffs.WHO_2016_EXPECTED_OVERRIDES",
        frozenset({"W260"}),
    )
    altered = apply_nhs_2016_alterations(records, place_modifiers)

    assert altered["W000"].description == "Fall on same level"
    assert altered["W000"].term_modifier == "Home"
    assert altered["W260"].description == "Contact with sharp objects"
    assert altered["W260"].term_modifier == "Home"
    assert "Y060" not in altered
    assert records["W260"].description == "Literal WHO subcategory"


def test_check_2016_claml_scraped_differences_fails_on_unknown_code():
    claml_records = {
        "A00": ICD10Code(code="A00", parent=None, description="Cholera"),
    }
    scraped_records = {}

    with pytest.raises(ValueError, match="Unexpected differences found"):
        check_diff_2016_claml_with_scraped(claml_records, scraped_records)


def test_build_2016_claml_scraped_diff_report_classifies_known_and_unknown_diffs():
    claml_records = {
        "A00": ICD10Code(code="A00", parent=None, description="Cholera"),
        "J10": ICD10Code(
            code="J10",
            parent=None,
            description="influenza due to identified seasonal influenza virus",
        ),
        "M1400": ICD10Code(code="M1400", parent="M140", description="Known only"),
        "UNKNOWN": ICD10Code(code="UNKNOWN", parent=None, description="Unknown only"),
        "BOTH": ICD10Code(code="BOTH", parent=None, description="In both the same"),
    }
    scraped_records = {
        "A00": ICD10Code(code="A00", parent=None, description="Cholera changed"),
        "J10": ICD10Code(
            code="J10",
            parent=None,
            description="Influenza due to identified seasonal influenza virus",
        ),
        "BOTH": ICD10Code(code="BOTH", parent=None, description="In both the same"),
    }

    report = build_2016_claml_scraped_diff_report(claml_records, scraped_records)

    assert report.claml_record_count == 5
    assert report.scraped_record_count == 3
    assert report.claml_only_codes == ["M1400", "UNKNOWN"]
    assert report.unexpected_claml_only_codes == ["UNKNOWN"]
    assert report.description_difference_count == 2
    assert report.unexpected_term_differences == [("A00", "Cholera", "Cholera changed")]
    assert report.has_unexpected_differences is True


def test_check_2016_claml_scraped_differences_prints_claml_only_output():
    claml_records = {
        "A00": ICD10Code(code="A00", parent=None, description="Cholera"),
    }
    scraped_records = {}

    with (
        pytest.raises(ValueError, match="Unexpected differences found"),
        structlog.testing.capture_logs() as captured_logs,
    ):
        check_diff_2016_claml_with_scraped(claml_records, scraped_records)

    output = flatten_logs(captured_logs)
    assert "CLAML-only codes" in output
    assert '"A00": CodeDifference(include_in_release=True/False),' in output
    assert "UNEXPECTED DIFFS FOUND" in output


def test_check_2016_claml_scraped_differences_prints_scraped_only_output():
    claml_records = {}
    scraped_records = {
        "A00": ICD10Code(code="A00", parent=None, description="Cholera"),
    }

    with (
        pytest.raises(ValueError, match="Unexpected differences found"),
        structlog.testing.capture_logs() as captured_logs,
    ):
        check_diff_2016_claml_with_scraped(claml_records, scraped_records)

    output = flatten_logs(captured_logs)
    assert "Scraped-only codes" in output
    assert '"A00": CodeDifference(include_in_release=True/False),' in output
    assert "UNEXPECTED DIFFS FOUND" in output


def test_check_2016_claml_scraped_differences_prints_description_differences():
    claml_records = {
        "A00": ICD10Code(code="A00", parent=None, description="Cholera"),
    }
    scraped_records = {
        "A00": ICD10Code(code="A00", parent=None, description="Cholera changed"),
    }

    with (
        pytest.raises(ValueError, match="Unexpected differences found"),
        structlog.testing.capture_logs() as captured_logs,
    ):
        check_diff_2016_claml_with_scraped(claml_records, scraped_records)

    output = flatten_logs(captured_logs)
    assert "Description (term) differences" in output
    assert '"A00": TermDifference(' in output
    assert "UNEXPECTED DIFFS FOUND" in output


def test_combine_2016_claml_and_scraped_records_uses_known_term_choice(monkeypatch):
    claml_records = {
        "J10": ICD10Code(
            code="J10",
            parent=None,
            description="influenza due to identified seasonal influenza virus",
        ),
    }
    scraped_records = {
        "J10": ICD10Code(
            code="J10",
            parent=None,
            description="Influenza due to identified seasonal influenza virus",
        ),
    }

    monkeypatch.setattr(
        "coding_systems.icd10.release_builder.apply_nhs_2016_alterations",
        lambda records, place_modifiers: records,
    )

    combined = combine_2016_claml_and_scraped_records(claml_records, scraped_records)

    assert combined["J10"] is scraped_records["J10"]


def test_combine_2016_claml_and_scraped_records_applies_derived_rubric_change(
    monkeypatch,
):
    claml_records = {
        "A00": ICD10Code(
            code="A00",
            parent=None,
            description="Cholera",
            concept_rubrics={
                "inclusion": ["Keep"],
                "exclusion": ["Remove"],
            },
        ),
    }
    scraped_records = {
        "A00": ICD10Code(
            code="A00",
            parent=None,
            description="Cholera",
            concept_rubrics={
                "inclusion": ["Keep"],
                "exclusion": ["Remove"],
            },
        ),
    }

    monkeypatch.setattr(
        "coding_systems.icd10.release_builder.check_diff_2016_claml_with_scraped",
        lambda claml, scraped: None,
    )
    monkeypatch.setattr(
        "coding_systems.icd10.release_builder.KNOWN_2016_RUBRIC_CHANGES",
        {
            "A00": RubricChange(
                who_2016={
                    "inclusion": ["Keep"],
                    "exclusion": ["Remove"],
                },
                remove={"exclusion": ["Remove"]},
            )
        },
    )

    combined = combine_2016_claml_and_scraped_records(claml_records, scraped_records)

    assert combined["A00"].concept_rubrics == {"inclusion": ["Keep"]}


def test_combine_2016_claml_and_scraped_records_rejects_unexpected_rubric(
    monkeypatch,
):
    claml_records = {
        "A00": ICD10Code(
            code="A00",
            parent=None,
            description="Cholera",
            concept_rubrics={"inclusion": ["Unexpected"]},
        ),
    }
    scraped_records = {
        "A00": ICD10Code(code="A00", parent=None, description="Cholera"),
    }

    monkeypatch.setattr(
        "coding_systems.icd10.release_builder.check_diff_2016_claml_with_scraped",
        lambda claml, scraped: None,
    )
    monkeypatch.setattr(
        "coding_systems.icd10.release_builder.KNOWN_2016_RUBRIC_CHANGES",
        {"A00": RubricChange(who_2016={"inclusion": ["Expected"]})},
    )

    with pytest.raises(ValueError, match="Unexpected rubric for A00"):
        combine_2016_claml_and_scraped_records(claml_records, scraped_records)


def test_combine_2016_claml_and_scraped_records_includes_and_excludes_known_only_codes(
    monkeypatch,
):
    claml_records = {
        "A00": ICD10Code(code="A00", parent=None, description="Cholera"),
        "C1": ICD10Code(code="C1", parent=None, description="Keep CLAML only"),
        "C2": ICD10Code(code="C2", parent=None, description="Drop CLAML only"),
    }
    scraped_records = {
        "A00": ICD10Code(code="A00", parent=None, description="Cholera"),
        "S1": ICD10Code(code="S1", parent=None, description="Keep scraped only"),
        "S2": ICD10Code(code="S2", parent=None, description="Drop scraped only"),
    }

    monkeypatch.setattr(
        "coding_systems.icd10.release_builder.apply_nhs_2016_alterations",
        lambda records, place_modifiers: records,
    )
    monkeypatch.setattr(
        "coding_systems.icd10.release_builder.check_diff_2016_claml_with_scraped",
        lambda claml, scraped: None,
    )
    monkeypatch.setattr(
        "coding_systems.icd10.release_builder.should_include_2016_claml_only",
        lambda code: code == "C1",
    )
    monkeypatch.setattr(
        "coding_systems.icd10.release_builder.should_include_2016_scraped_only",
        lambda code: code == "S1",
    )

    combined = combine_2016_claml_and_scraped_records(claml_records, scraped_records)

    assert set(combined) == {"A00", "C1", "S1"}
    assert combined["A00"] == scraped_records["A00"]
    assert combined["C1"] == claml_records["C1"]
    assert combined["S1"] == scraped_records["S1"]


def test_check_2016_claml_scraped_differences_passes_when_differences_are_known():
    claml_records = {
        "J10": ICD10Code(
            code="J10",
            parent=None,
            description="influenza due to identified seasonal influenza virus",
        ),
    }
    scraped_records = {
        "J10": ICD10Code(
            code="J10",
            parent=None,
            description="Influenza due to identified seasonal influenza virus",
        ),
    }
    with structlog.testing.capture_logs() as captured_logs:
        differences = check_diff_2016_claml_with_scraped(claml_records, scraped_records)

    assert differences is None
    output = flatten_logs(captured_logs)

    assert "ALL OK" in output


def test_check_2016_2019_differences_fails_on_unknown_term_change():
    combined_2016_records = {
        "A00": ICD10Code(code="A00", parent=None, description="Cholera"),
    }
    who_2019_records = {
        "A00": ICD10Code(code="A00", parent=None, description="Different cholera"),
    }

    with pytest.raises(ValueError, match="Unexpected differences found"):
        check_diff_2016_with_2019(combined_2016_records, who_2019_records)


def test_check_2016_2019_differences_prints_actionable_output():
    combined_2016_records = {
        "A00": ICD10Code(code="A00", parent=None, description="Cholera"),
    }
    who_2019_records = {
        "A00": ICD10Code(code="A00", parent=None, description="Different cholera"),
    }

    with (
        pytest.raises(ValueError, match="Unexpected differences found"),
        structlog.testing.capture_logs() as captured_logs,
    ):
        check_diff_2016_with_2019(combined_2016_records, who_2019_records)

    output = flatten_logs(captured_logs)
    assert "Compared combined 2016 ICD-10 records with WHO 2019 ClaML" in output
    assert "Description (term) differences" in output
    assert '"A00": ReleaseTermDifference(' in output
    assert "UNEXPECTED DIFFS FOUND" in output


def test_build_2016_2019_diff_report_classifies_known_and_unknown_diffs():
    combined_2016_records = {
        "A00": ICD10Code(code="A00", parent=None, description="Cholera"),
        "A081": ICD10Code(
            code="A081",
            parent=None,
            description="Acute gastroenteropathy due to Norwalk agent",
        ),
        "W260": ICD10Code(
            code="W260",
            parent="W26",
            description="Contact with other sharp object(s)",
            term_modifier="Home",
        ),
        "ONLY16": ICD10Code(code="ONLY16", parent=None, description="Only 2016"),
        "BOTH": ICD10Code(code="BOTH", parent=None, description="In both the same"),
    }
    who_2019_records = {
        "A00": ICD10Code(code="A00", parent=None, description="Changed cholera"),
        "A081": ICD10Code(
            code="A081",
            parent=None,
            description="Acute gastroenteropathy due to Norovirus",
        ),
        "W260": ICD10Code(
            code="W260",
            parent="W26",
            description="Contact with knife, sword or dagger",
        ),
        "ONLY19": ICD10Code(code="ONLY19", parent=None, description="Only 2019"),
        "BOTH": ICD10Code(code="BOTH", parent=None, description="In both the same"),
    }

    report = build_2016_2019_diff_report(combined_2016_records, who_2019_records)

    assert report.combined_2016_only_codes == ["ONLY16"]
    assert report.who_2019_only_codes == ["ONLY19"]
    assert report.clinically_equivalent_description_difference_count == 1
    assert report.clinically_different_description_difference_count == 1
    assert report.unexpected_description_differences == [
        ("A00", "Cholera", "Changed cholera")
    ]
    assert report.description_difference_count == 3
    assert report.has_unexpected_differences is True


def test_check_2016_2019_differences_counts_known_equivalent_and_different_changes():
    combined_2016_records = {
        "A081": ICD10Code(
            code="A081",
            parent=None,
            description="Acute gastroenteropathy due to Norwalk agent",
        ),
        "W260": ICD10Code(
            code="W260",
            parent="W26",
            description="Contact with other sharp object(s)",
            term_modifier="Home",
        ),
    }
    who_2019_records = {
        "A081": ICD10Code(
            code="A081",
            parent=None,
            description="Acute gastroenteropathy due to Norovirus",
        ),
        "W260": ICD10Code(
            code="W260",
            parent="W26",
            description="Contact with knife, sword or dagger",
        ),
    }
    with structlog.testing.capture_logs() as captured_logs:
        differences = check_diff_2016_with_2019(combined_2016_records, who_2019_records)

    assert differences is None

    output = flatten_logs(captured_logs)
    assert "Clinically equivalent:  1" in output
    assert "Clinically different:   1" in output
    assert "ALL OK" in output


def test_load_import_records_builds_2016_and_2019_outputs(monkeypatch, dummy_zip):
    parsed_records = {
        "A00": ICD10Code(code="A00", parent=None, description="Cholera"),
    }

    def fake_parse_claml(xml_path):
        return parsed_records, []

    def fake_apply_nhs_2016_alterations(records, place_modifiers):
        return records

    monkeypatch.setattr(
        "coding_systems.icd10.release_builder.parse_claml",
        fake_parse_claml,
    )
    monkeypatch.setattr(
        "coding_systems.icd10.release_builder.apply_nhs_2016_alterations",
        fake_apply_nhs_2016_alterations,
    )
    monkeypatch.setattr(
        "coding_systems.icd10.release_builder.combine_2016_claml_and_scraped_records",
        lambda who_2016_records, scraped_2016_records: parsed_records,
    )
    monkeypatch.setattr(
        "coding_systems.icd10.release_builder.check_diff_2016_with_2019",
        lambda output_2016, output_2019: None,
    )
    zip_path, file_metadata = dummy_zip
    output_2016, output_2019 = load_import_records(zip_path, file_metadata)

    assert output_2016 == parsed_records
    assert output_2019 == parsed_records


def test_load_import_records_raises_when_release_diff_check_fails(
    monkeypatch, dummy_zip
):
    parsed_records = {
        "A00": ICD10Code(code="A00", parent=None, description="Cholera"),
    }

    def fake_apply_nhs_2016_alterations(records, place_modifiers):
        return records

    monkeypatch.setattr(
        "coding_systems.icd10.release_builder.parse_claml",
        lambda xml_path: (parsed_records, []),
    )
    monkeypatch.setattr(
        "coding_systems.icd10.release_builder.apply_nhs_2016_alterations",
        fake_apply_nhs_2016_alterations,
    )
    monkeypatch.setattr(
        "coding_systems.icd10.release_builder.combine_2016_claml_and_scraped_records",
        lambda who_2016_records, scraped_2016_records: parsed_records,
    )
    monkeypatch.setattr(
        "coding_systems.icd10.release_builder.check_diff_2016_with_2019",
        lambda output_2016, output_2019: (_ for _ in ()).throw(ValueError("bad diff")),
    )

    with pytest.raises(ValueError, match="bad diff"):
        zip_path, file_metadata = dummy_zip
        load_import_records(zip_path, file_metadata)


def test_load_import_records_applies_nhs_alterations_before_combining(
    monkeypatch, dummy_zip
):
    who_2016 = {
        "W00": ICD10Code(code="W00", parent=None, description="Fall on same level"),
    }
    who_2019 = {
        "A00": ICD10Code(code="A00", parent=None, description="Cholera"),
    }
    nhs_2016 = {
        "B00": ICD10Code(code="B00", parent=None, description="NHS record"),
    }
    place_modifiers = [ModifierDigit(digit_code="0", description="Home")]

    def fake_parse_claml(xml_path):
        if xml_path.name == "icd102016en.xml":
            return who_2016, place_modifiers
        if xml_path.name == "icd102019en.xml":
            return who_2019, []
        if xml_path.name == "icd10nhs2016en.xml":
            return nhs_2016, []
        raise AssertionError(xml_path)

    combined = {
        "W000": ICD10Code(
            code="W000",
            parent="W00",
            description="Fall on same level",
            term_modifier="Home",
            modifier_position=4,
        )
    }
    seen = {}

    def fake_combine(who_2016_records, scraped_2016_records):
        seen["who_2016_records"] = who_2016_records
        seen["scraped_2016_records"] = scraped_2016_records
        return combined

    monkeypatch.setattr(
        "coding_systems.icd10.release_builder.parse_claml", fake_parse_claml
    )
    monkeypatch.setattr(
        "coding_systems.icd10.release_builder.combine_2016_claml_and_scraped_records",
        fake_combine,
    )
    monkeypatch.setattr(
        "coding_systems.icd10.release_builder.check_diff_2016_with_2019",
        lambda output_2016, output_2019: None,
    )
    monkeypatch.setattr(
        "coding_systems.icd10.known_diffs.WHO_2016_EXPECTED_OVERRIDES",
        frozenset(),
    )

    zip_path, file_metadata = dummy_zip
    output_2016, output_2019 = load_import_records(zip_path, file_metadata)

    assert "W000" in seen["who_2016_records"]
    assert seen["who_2016_records"]["W000"].term_modifier == "Home"
    assert seen["scraped_2016_records"] is nhs_2016
    assert output_2016 is combined
    assert output_2019 is who_2019
