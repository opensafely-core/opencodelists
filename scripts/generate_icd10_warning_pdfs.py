"""Create the manual ICD-10 codelist issue report bundle.

Run with:

    python scripts/generate_icd10_warning_pdfs.py \
        db.sqlite3 icd10.sqlite3 old-icd10.sqlite3
"""

import argparse
import sqlite3
import sys
from pathlib import Path


# Make direct execution resolve project and ``scripts`` package imports.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.icd10_reports.data import (
    find_affected_codelists,
    issues_by_code,
    load_codes,
    load_modifier_descendants,
    reports_by_owner,
)
from scripts.icd10_reports.output import write_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "database", type=Path, help="OpenCodelists core SQLite database"
    )
    parser.add_argument(
        "icd10_database",
        type=Path,
        help="Current imported ICD-10 release SQLite database",
    )
    parser.add_argument(
        "old_icd10_database",
        type=Path,
        help="Previous ICD-10 release SQLite database",
    )
    args = parser.parse_args()

    try:
        with sqlite3.connect(
            f"file:{args.old_icd10_database.resolve()}?mode=ro", uri=True
        ) as old_icd10_connection:
            old_codes = load_codes(old_icd10_connection)

            # double check we're loading the correct DB
            assert len(old_codes) == 12593
        with sqlite3.connect(
            f"file:{args.icd10_database.resolve()}?mode=ro", uri=True
        ) as icd10_connection:
            current_codes = load_codes(icd10_connection)
            modifier_descendants = load_modifier_descendants(
                icd10_connection, old_codes
            )

            # double check we're loading the correct DB
            assert len(modifier_descendants) == 753
        with sqlite3.connect(
            f"file:{args.database.resolve()}?mode=ro", uri=True
        ) as connection:
            affected = find_affected_codelists(connection, modifier_descendants)
            reports = reports_by_owner(connection, affected)
        code_issues = issues_by_code(old_codes | current_codes, modifier_descendants)
        write_outputs(reports, affected, code_issues)
    except RuntimeError as error:
        parser.error(str(error))

    user_count = sum(owner.kind == "user" for owner in reports)
    organisation_count = sum(owner.kind == "organisation" for owner in reports)
    print(f"Found {len(affected)} affected codelists.")
    print(
        f"Wrote {user_count} user PDFs, {organisation_count} organisation PDFs, "
        f"recipients.csv, summary.md, issues.json, and example.pdf."
    )


if __name__ == "__main__":
    main()
