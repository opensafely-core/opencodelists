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
