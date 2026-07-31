import csv
import json
import shutil
from pathlib import Path

from .example import load_example_codelists
from .models import AffectedCodelist, ReportOwner
from .rendering import BASE_URL, render_report, render_summary, write_pdf


CSV_FIELDS = ("email", "pdf_filename")


def write_outputs(
    reports: dict[ReportOwner, list[AffectedCodelist]],
    affected: list[AffectedCodelist],
    code_issues: dict[str, list[dict[str, object]]],
) -> None:
    """Write the complete manual report bundle."""
    output_dir = Path(__file__).parent / "reports"
    _prepare_output_dir(output_dir)
    csv_rows = []

    for owner, codelists in sorted(
        reports.items(), key=lambda item: (item[0].kind, item[0].identifier)
    ):
        owner_directory = "users" if owner.kind == "user" else "organisations"
        pdf_relative = Path(owner_directory) / f"{owner.identifier}.pdf"
        write_pdf(
            render_report(codelists),
            output_dir / pdf_relative,
        )

        if owner.kind == "user":
            csv_rows.append(
                {
                    "email": owner.email or "",
                    "pdf_filename": pdf_relative.as_posix(),
                }
            )

    csv_path = output_dir / "recipients.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(csv_rows)

    (output_dir / "summary.md").write_text(
        render_summary(reports, affected),
        encoding="utf-8",
    )
    write_issues_json(output_dir / "issues.json", affected, code_issues)
    write_pdf(
        render_report(load_example_codelists()),
        output_dir / "example.pdf",
    )


def write_issues_json(
    path: Path,
    affected: list[AffectedCodelist],
    code_issues: dict[str, list[dict[str, object]]],
) -> None:
    """Write a PII-free lookup of warnings by codelist URL and inline code."""
    codelists: dict[str, list[dict[str, object]]] = {}
    for codelist in affected:
        issues: list[dict[str, object]] = []
        for code, change in sorted(codelist.description_changes.items()):
            issues.append(
                {
                    "type": "description_change",
                    "code": code,
                    **change,
                }
            )
        for moved_code_set in codelist.moved_code_sets:
            possible_codes = set(moved_code_set["nhs2016"]) | set(
                moved_code_set["who2019"]
            )
            issues.append(
                {
                    "type": "moved_codes",
                    "title": moved_code_set["title"],
                    "comment": moved_code_set["comment"],
                    "nhs2016": sorted(moved_code_set["nhs2016"]),
                    "who2019": sorted(moved_code_set["who2019"]),
                    "codes_found": sorted(codelist.codes & possible_codes),
                    "codes_missing": sorted(possible_codes - codelist.codes),
                }
            )
        for code, modifier_codes in sorted(codelist.missing_modifier_codes.items()):
            issues.append(
                {
                    "type": "missing_modifier_codes",
                    "code": code,
                    "modifier_codes": sorted(modifier_codes),
                }
            )

        for version_path in codelist.version_paths():
            codelists[f"{BASE_URL}{version_path}"] = issues

    document = {
        "schema_version": 1,
        "codelists": codelists,
        "codes": code_issues,
    }
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _prepare_output_dir(output_dir: Path) -> None:
    output_dir = output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
