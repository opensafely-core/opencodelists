"""Tests for CSV structure detection logic."""

import pytest

from opencodelists.views.user_create_codelist import (
    _detect_code_column_header_and_system,
)


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
