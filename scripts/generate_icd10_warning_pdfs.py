"""Create the manual ICD-10 codelist issue report bundle.

Run with:

    python scripts/report_icd10_codelist_issues.py db.sqlite3
"""

import argparse
import sqlite3
import sys
from pathlib import Path


# Make direct execution resolve project and ``scripts`` package imports.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.icd10_reports.data import find_affected_codelists, reports_by_owner
from scripts.icd10_reports.output import write_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "database", type=Path, help="OpenCodelists core SQLite database"
    )
    args = parser.parse_args()

    try:
        with sqlite3.connect(
            f"file:{args.database.resolve()}?mode=ro", uri=True
        ) as connection:
            affected = find_affected_codelists(connection)
            reports = reports_by_owner(connection, affected)
        write_outputs(reports, affected)
    except RuntimeError as error:
        parser.error(str(error))

    user_count = sum(owner.kind == "user" for owner in reports)
    organisation_count = sum(owner.kind == "organisation" for owner in reports)
    print(f"Found {len(affected)} affected codelists.")
    print(
        f"Wrote {user_count} user PDFs, {organisation_count} organisation PDFs, "
        f"recipients.csv, summary.md, and example.pdf."
    )


if __name__ == "__main__":
    main()
