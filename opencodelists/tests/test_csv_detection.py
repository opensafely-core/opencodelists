"""Tests for CSV structure detection logic."""

from io import BytesIO

import pytest

from opencodelists.views.user_create_codelist import (
    _detect_code_column_header_and_system,
)


class TestCSVDetection:
    """Tests for _detect_code_column_header_and_system function (parametrized)."""

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "rows,expected_first,expected_code_column,expected_coding_system",
        [
            # Simple CSV with codes only - no header
            (
                [
                    ["429554009", "Arthropathy of elbow"],
                    ["128133004", "Disorder of elbow"],
                    ["202855006", "Lateral epicondylitis"],
                ],
                0,
                0,
                "snomedct",
            ),
            # CSV with header
            (
                [
                    ["code", "description"],
                    ["429554009", "Arthropathy of elbow"],
                    ["128133004", "Disorder of elbow"],
                ],
                1,
                0,
                "snomedct",
            ),
            # Empty CSV
            (
                [],
                0,
                0,
                None,
            ),
            # Single row with a valid code
            (
                [["429554009", "Arthropathy of elbow"]],
                0,
                0,
                "snomedct",
            ),
            # Multiple lines header before codes
            (
                [
                    ["This is a description of the codelist"],
                    ["It contains important clinical codes"],
                    ["code", "description"],
                    ["429554009", "Arthropathy of elbow"],
                    ["128133004", "Disorder of elbow"],
                ],
                3,
                0,
                "snomedct",
            ),
            # Free text line then codes
            (
                [
                    ["Exported from system on 2026-01-08"],
                    ["429554009", "Arthropathy of elbow"],
                ],
                1,
                0,
                "snomedct",
            ),
            # Multi-line free text then codes
            (
                [
                    ["Clinical Codelist Export"],
                    ["Generated: 2026-01-08"],
                    ["User: Dr Smith"],
                    [""],
                    ["code", "term", "status"],
                    ["429554009", "Arthropathy of elbow", "active"],
                ],
                5,
                0,
                "snomedct",
            ),
            # Codes in second column without header
            (
                [
                    ["Description", "429554009"],
                    ["Some text", "128133004"],
                    ["More text", "202855006"],
                ],
                0,
                1,
                "snomedct",
            ),
            # Codes in second column with header row
            (
                [
                    ["Description", "Code"],
                    ["Some text", "128133004"],
                    ["More text", "202855006"],
                ],
                1,
                1,
                "snomedct",
            ),
            # No valid rows returns defaults
            (
                [
                    ["not", "a", "code"],
                    ["also", "not", "valid"],
                    ["still", "nothing", "here"],
                ],
                0,
                0,
                None,
            ),
        ],
    )
    def test_detect_code_column_header_and_system(
        self,
        snomedct_data,
        rows,
        expected_first,
        expected_code_column,
        expected_coding_system,
    ):
        first_data_row_idx, code_col, detected_coding_system = (
            _detect_code_column_header_and_system(rows)
        )
        assert first_data_row_idx == expected_first
        assert code_col == expected_code_column
        assert detected_coding_system == expected_coding_system


class TestIntegratedDetection:
    """Integration tests for full CSV detection flow."""

    @pytest.mark.django_db
    def test_simple_csv_no_header_snomed(
        self, client, user_without_organisation, snomedct_data
    ):
        """Test simple CSV without header using valid SNOMED codes."""
        csv_content = b"429554009,Arthropathy of elbow\n128133004,Disorder of elbow\n202855006,Lateral epicondylitis"
        csv_file = BytesIO(csv_content)
        csv_file.name = "test.csv"

        client.force_login(user_without_organisation)
        response = client.post(
            "/users/dave/csv-descendants-preview/",
            {
                "csv_data": csv_file,
                "coding_system_id": "snomedct",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["detected_first_data_row"] == 0
        assert data["detected_code_column"] == 0
        assert data["detected_coding_system_id"] == "snomedct"

    @pytest.mark.django_db
    def test_csv_with_header(self, client, user_without_organisation, snomedct_data):
        """CSV with header row."""
        csv_content = b"code,description\n429554009,Arthropathy of elbow\n128133004,Disorder of elbow"
        csv_file = BytesIO(csv_content)
        csv_file.name = "test.csv"

        client.force_login(user_without_organisation)
        response = client.post(
            "/users/dave/csv-descendants-preview/",
            {
                "csv_data": csv_file,
                "coding_system_id": "snomedct",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["detected_first_data_row"] == 1
        assert data["detected_code_column"] == 0
        assert data["detected_coding_system_id"] == "snomedct"

    @pytest.mark.django_db
    def test_auto_detect_code_column(
        self, client, user_without_organisation, snomedct_data
    ):
        """Auto-detect code column when not first."""
        csv_content = b"Description,429554009\nTerm,128133004\nMore,202855006"
        csv_file = BytesIO(csv_content)
        csv_file.name = "test.csv"

        client.force_login(user_without_organisation)
        response = client.post(
            "/users/dave/csv-descendants-preview/",
            {"csv_data": csv_file},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["detected_first_data_row"] == 0
        assert data["detected_code_column"] == 1
        assert data["detected_coding_system_id"] == "snomedct"

    @pytest.mark.django_db
    def test_parent_with_missing_immediate_children_with_duplicates(
        self, client, user_without_organisation, snomedct_data
    ):
        """Test that parent codes with missing immediate children are detected
        correctly even when codes are duplicated in the CSV.

        This tests the fix for the bug where iterating over the codes list
        (which can have duplicates) instead of code_set caused codes to be
        missed when checking for missing immediate children.

        Uses test SNOMED CT hierarchy:
        - 128133004 (Disorder of elbow) has immediate children including:
          - 429554009 (Arthropathy of elbow)
          - 35185008 (Enthesopathy of elbow region)
          - 239964003 (Soft tissue lesion of elbow region)

        If 128133004 is in the CSV (appearing multiple times) but 429554009
        is not, then 128133004 should appear in parent_examples.
        """
        # CSV with 128133004 appearing multiple times (simulating duplicate rows)
        # but NOT including its immediate child 429554009
        csv_content = b"128133004,Disorder of elbow\n128133004,Disorder of elbow\n35185008,Enthesopathy of elbow region"
        csv_file = BytesIO(csv_content)
        csv_file.name = "test.csv"

        client.force_login(user_without_organisation)
        response = client.post(
            "/users/dave/csv-descendants-preview/",
            {
                "csv_data": csv_file,
                "coding_system_id": "snomedct",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Should detect parent examples because 128133004 has missing immediate children
        parent_examples = data.get("parent_examples", [])
        assert len(parent_examples) > 0, (
            "Should find at least one parent with missing immediate children"
        )

        # Check that 128133004 is in the parent examples
        parent_codes = [ex["parent_code"] for ex in parent_examples]
        assert "128133004" in parent_codes, (
            "128133004 should be in parent_examples as it has missing immediate children"
        )

        # Find the example for 128133004 and verify it has immediate children info
        example_128133004 = next(
            (ex for ex in parent_examples if ex["parent_code"] == "128133004"), None
        )
        assert example_128133004 is not None

        immediate_children = example_128133004["immediate_children"]
        assert len(immediate_children) > 0, (
            "128133004 should have immediate children listed"
        )

        # Verify that 429554009 is listed as an immediate child that is NOT present
        child_429554009 = next(
            (child for child in immediate_children if child["code"] == "429554009"),
            None,
        )
        assert child_429554009 is not None, (
            "429554009 should be listed as an immediate child"
        )
        assert child_429554009["present"] is False, (
            "429554009 should be marked as NOT present in the CSV"
        )

        # Verify that 35185008 IS present (it's in the CSV)
        child_35185008 = next(
            (child for child in immediate_children if child["code"] == "35185008"), None
        )
        assert child_35185008 is not None, (
            "35185008 should be listed as an immediate child"
        )
        assert child_35185008["present"] is True, (
            "35185008 should be marked as present in the CSV"
        )
