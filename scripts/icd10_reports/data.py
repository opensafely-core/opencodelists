import csv
import sqlite3
from collections import defaultdict
from io import StringIO

from coding_systems.icd10.known_diffs import clinically_different_codes, moved_codes

from .models import AffectedCodelist, ReportOwner


INCLUDED_STATUSES = ("+", "(+)")


def codes_from_csv(csv_data: str) -> set[str]:
    """Extract codes from old-style codelists with CSV data stored in the database."""
    rows = list(csv.reader(StringIO(csv_data)))
    if len(rows) < 2:
        return set()

    headers = [header.lower().strip() for header in rows[0]]

    # Find first column that looks like an ICD-10 code, falling back to first column (
    # some don't have a header). Where headers exist these 5 are the only ones seen in the data
    code_index = 0
    for header in ["icd10_code", "icd code", "icd_code", "icd", "code"]:
        if header in headers:
            code_index = headers.index(header)
            break

    return {
        row[code_index].strip()
        for row in rows[1:]
        if len(row) > code_index and row[code_index].strip()
    }


def incomplete_moved_code_sets(codes: set[str]) -> list[dict[str, object]]:
    """Return moved-code groups for which this codelist includes only some codes."""
    incomplete = []
    for moved_code_set in moved_codes(codes):
        possible_codes = set(moved_code_set["nhs2016"]) | set(moved_code_set["who2019"])
        missing_codes = possible_codes - codes
        if missing_codes:
            incomplete.append(moved_code_set)
    return incomplete


def find_affected_codelists(
    connection: sqlite3.Connection,
) -> list[AffectedCodelist]:
    connection.row_factory = sqlite3.Row
    rows = connection.execute(
        """
        WITH latest_versions AS (
            SELECT codelist_id, MAX(id) AS version_id
            FROM codelists_codelistversion
            GROUP BY codelist_id
        )
        SELECT
            c.id,
            h.name,
            h.slug,
            h.user_id,
            h.organisation_id,
            v.id AS version_id,
            v.tag AS version_tag,
            v.csv_data
        FROM codelists_codelist AS c
        JOIN codelists_handle AS h
          ON h.codelist_id = c.id AND h.is_current = 1
        JOIN latest_versions AS latest ON latest.codelist_id = c.id
        JOIN codelists_codelistversion AS v ON v.id = latest.version_id
        WHERE c.coding_system_id = 'icd10'
        ORDER BY h.organisation_id, h.user_id, h.slug
        """
    ).fetchall()

    new_style_version_ids = [
        row["version_id"] for row in rows if row["csv_data"] is None
    ]
    codes_by_version: dict[int, set[str]] = defaultdict(set)
    if new_style_version_ids:
        placeholders = ",".join("?" for _ in new_style_version_ids)
        code_rows = connection.execute(
            f"""
            SELECT version_id, code
            FROM codelists_codeobj
            WHERE version_id IN ({placeholders})
              AND status IN (?, ?)
            """,  # noqa: S608 - placeholders are generated, not user supplied
            (*new_style_version_ids, *INCLUDED_STATUSES),
        )
        for code_row in code_rows:
            codes_by_version[code_row["version_id"]].add(code_row["code"])

    affected = []
    for row in rows:
        codes = (
            codes_from_csv(row["csv_data"])
            if row["csv_data"] is not None
            else codes_by_version[row["version_id"]]
        )
        description_changes = clinically_different_codes(list(codes))
        moved_code_sets = incomplete_moved_code_sets(codes)
        if description_changes or moved_code_sets:
            affected.append(
                AffectedCodelist(
                    name=row["name"],
                    slug=row["slug"],
                    user_id=row["user_id"],
                    organisation_id=row["organisation_id"],
                    version_id=row["version_id"],
                    version_tag=row["version_tag"],
                    codes=frozenset(code.upper() for code in codes),
                    description_changes=description_changes,
                    moved_code_sets=moved_code_sets,
                )
            )
    return affected


def reports_by_owner(
    connection: sqlite3.Connection,
    affected: list[AffectedCodelist],
) -> dict[ReportOwner, list[AffectedCodelist]]:
    """Group actionable codelists by their direct user or organisation owner."""
    connection.row_factory = sqlite3.Row
    user_ids = {item.user_id for item in affected if item.user_id}
    organisation_ids = {
        item.organisation_id for item in affected if item.organisation_id
    }

    owners: dict[tuple[str, str], ReportOwner] = {}
    if user_ids:
        placeholders = ",".join("?" for _ in user_ids)
        rows = connection.execute(
            f"""
            SELECT username, name, email
            FROM opencodelists_user
            WHERE username IN ({placeholders})
            """,  # noqa: S608 - placeholders are generated, not user supplied
            tuple(sorted(user_ids)),
        )
        for row in rows:
            owner = ReportOwner(
                kind="user",
                identifier=row["username"],
                name=row["name"],
                email=row["email"],
            )
            owners[(owner.kind, owner.identifier)] = owner

    if organisation_ids:
        placeholders = ",".join("?" for _ in organisation_ids)
        rows = connection.execute(
            f"""
            SELECT slug, name
            FROM opencodelists_organisation
            WHERE slug IN ({placeholders})
            """,  # noqa: S608 - placeholders are generated, not user supplied
            tuple(sorted(organisation_ids)),
        )
        for row in rows:
            owner = ReportOwner(
                kind="organisation",
                identifier=row["slug"],
                name=row["name"],
            )
            owners[(owner.kind, owner.identifier)] = owner

    reports: dict[ReportOwner, list[AffectedCodelist]] = defaultdict(list)
    for codelist in affected:
        owner_key = (
            ("user", codelist.user_id)
            if codelist.user_id
            else ("organisation", codelist.organisation_id or "")
        )
        reports[owners[owner_key]].append(codelist)

    return dict(reports)
