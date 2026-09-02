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
from scripts.icd10_reports.email import send_emails
from scripts.icd10_reports.output import write_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "database",
        type=Path,
        help="OpenCodelists core SQLite database",
        nargs="?",
        default=None,
    )
    parser.add_argument(
        "icd10_database",
        type=Path,
        help="Current imported ICD-10 release SQLite database",
        nargs="?",
        default=None,
    )
    parser.add_argument(
        "old_icd10_database",
        type=Path,
        help="Previous ICD-10 release SQLite database",
        nargs="?",
        default=None,
    )
    parser.add_argument(
        "--bypass-generation",
        action="store_true",
        help="Do not generate new reports",
    )
    parser.add_argument(
        "--send-emails",
        action="store_true",
        help="Send emails to affected codelist owners",
    )
    parser.add_argument(
        "--no-dry-run",
        action="store_true",
        help="Actually send emails, default is to just print the recipients",
    )
    parser.add_argument(
        "--all-recipients",
        action="store_true",
        help="Send emails to all recipients, not just those in the SEED_EMAILS environment variable",
    )
    args = parser.parse_args()

    if args.bypass_generation and not args.send_emails:
        parser.error(
            "No action to take. Use --send-emails to send emails or remove --bypass-generation to generate reports."
        )

    if not args.bypass_generation and not all(
        [args.database, args.icd10_database, args.old_icd10_database]
    ):
        parser.error(
            "database, icd10_database, and old_icd10_database are required unless --bypass-generation is used"
        )

    if not args.send_emails:
        if args.no_dry_run:
            parser.error("--dry-run can only be used with --send-emails")
        if args.all_recipients:
            parser.error("--all-recipients can only be used with --send-emails")

    if not args.bypass_generation:
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
            code_issues = issues_by_code(
                old_codes | current_codes, modifier_descendants
            )
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
    if args.send_emails:
        results = send_emails(
            only_seeds=not args.all_recipients,
            dry_run=not args.no_dry_run,
        )
        if results:
            print("Mailgun API responses:")
            for email, response in results:
                print(f"{email}: {response}")


if __name__ == "__main__":
    main()
