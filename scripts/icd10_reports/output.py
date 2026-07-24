import csv
import shutil
from pathlib import Path

from .example import load_example_codelists
from .models import AffectedCodelist, ReportOwner
from .rendering import render_report, render_summary, write_pdf


CSV_FIELDS = ("email", "pdf_filename")


def write_outputs(
    reports: dict[ReportOwner, list[AffectedCodelist]], affected: list[AffectedCodelist]
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
    write_pdf(
        render_report(load_example_codelists()),
        output_dir / "example.pdf",
    )


def _prepare_output_dir(output_dir: Path) -> None:
    output_dir = output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
