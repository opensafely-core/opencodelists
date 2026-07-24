import html
import re
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

import markdown2

from .models import AffectedCodelist, ReportOwner


BASE_URL = "https://www.opencodelists.org"
PDF_CSS = """
@page {
  size: A4;
  margin: 18mm 16mm;
}
body {
  color: #1f2933;
  font-family: Arial, Helvetica, sans-serif;
  font-size: 10.5pt;
  line-height: 1.45;
  margin: 0;
}
h1, h2, h3 {
  color: #102a43;
  line-height: 1.2;
  page-break-after: avoid;
}
h1 { font-size: 22pt; margin: 0 0 18pt; }
h2 { border-bottom: 1px solid #bcccdc; font-size: 16pt; margin-top: 22pt; }
h3 { font-size: 12pt; margin-bottom: 5pt; }
a { color: #0967a8; text-decoration: none; }
li { margin: 3pt 0; }
code {
  background: #f0f4f8;
  border-radius: 2px;
  font-family: "Liberation Mono", monospace;
  font-size: 9.5pt;
  padding: 1px 3px;
}
p, li { orphans: 3; widows: 3; }
"""
MARKDOWN_SPECIAL_CHARS = re.compile(r"([\\`*_{}\[\]()<>#+\-.!>])")


def escape_markdown(value: object) -> str:
    """Escape plain text before interpolating it into Markdown."""
    return MARKDOWN_SPECIAL_CHARS.sub(r"\\\1", str(value))


def code_span(value: object) -> str:
    """Wrap plain text in a Markdown code span."""
    text = str(value)
    longest_run = max((len(run) for run in re.findall(r"`+", text)), default=0)
    delimiter = "`" * (longest_run + 1)
    padding = " " if text.startswith("`") or text.endswith("`") else ""
    return f"{delimiter}{padding}{text}{padding}{delimiter}"


def render_report(codelists: list[AffectedCodelist]) -> str:
    lines = [
        "# Your ICD-10 codelists that require review",
        "",
        f"_Generated on {datetime.now().strftime('%Y-%m-%d')}_",
        "",
        "Following the new **ICD-10 OpenSAFELY** release on OpenCodelists, "
        "we've identified one or more of your ICD-10 codelists that should be "
        "reviewed.",
        "",
        "**This report only lists the codelists we've identified as requiring "
        "review**. It explains why each has been flagged and provides links to "
        "open them in OpenCodelists.",
        "",
        "For each affected codelist:",
        "",
        "1. Open the codelist.",
        "2. Create a new version. (Creating a new version will leave your "
        "existing codelist version unchanged.)",
        "3. Follow the guidance in OpenCodelists to review any highlighted "
        "codes before publishing the updated version.",
        "",
    ]

    changed_descriptions = [c for c in codelists if c.description_changes]
    if changed_descriptions:
        lines.extend(
            [
                "## Action required: code descriptions differ",
                "",
                "The following codelist(s) have codes whose description in the "
                "2016 release of ICD-10 (used in APCS admissions data) differs "
                "from the description in the 2019 release (used in ONS deaths "
                "data). If you include these codes in your codelist they may not "
                "match the events you expect depending on which data source you "
                "are targeting. OpenCodelists will highlight these codes when you "
                "review the codelist and explain the differences between the "
                "ICD-10 releases.",
                "",
            ]
        )
        for codelist in sorted(
            changed_descriptions,
            key=lambda item: (item.name.lower(), item.slug.lower()),
        ):
            url = f"{BASE_URL}{codelist.path()}"
            lines.extend([f"### [{escape_markdown(codelist.name)}]({url})", ""])
            for code, change in sorted(codelist.description_changes.items()):
                lines.extend(
                    [
                        f"- {code_span(code)}:",
                        "  - NHS 2016 definition: "
                        f"{escape_markdown(change['combined_2016'])}",
                        "  - WHO 2019 definition: "
                        f"{escape_markdown(change['who_2019'])}",
                    ]
                )
            lines.append("")

    moved_code_codelists = [c for c in codelists if c.moved_code_sets]
    if moved_code_codelists:
        lines.extend(
            [
                "## Action recommended: codes may be missing",
                "",
                "The following codelist(s) have codes that have changed between "
                "the 2016 release of ICD-10 (used in APCS admissions data) and "
                "the 2019 release (used in ONS deaths data). We have found that "
                "some of your codelists contain one of these codes from one "
                "release, but not the equivalent code from the other release. By "
                "not including the missing code, you may miss events depending on "
                "which data table you are targeting. OpenCodelists will highlight "
                "these codes when you review the codelist and help you identify "
                "any equivalent codes that may need to be added.",
                "",
            ]
        )
        for codelist in sorted(
            moved_code_codelists,
            key=lambda item: (item.name.lower(), item.slug.lower()),
        ):
            url = f"{BASE_URL}{codelist.path()}"
            lines.extend([f"### [{escape_markdown(codelist.name)}]({url})", ""])
            for moved in codelist.moved_code_sets:
                possible_codes = set(moved["nhs2016"]) | set(moved["who2019"])
                matched_codes = ", ".join(
                    code_span(code) for code in sorted(codelist.codes & possible_codes)
                )
                missing_codes = possible_codes - codelist.codes
                missing = ", ".join(code_span(code) for code in sorted(missing_codes))
                lines.extend(
                    [
                        f"- **{escape_markdown(moved['title'])}**: "
                        f"{escape_markdown(moved['comment'])}",
                        f"  - Codes found in this codelist: {matched_codes}",
                        f"  - Codes potentially missing from this codelist: {missing}",
                    ]
                )
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_summary(
    reports: dict[ReportOwner, list[AffectedCodelist]], affected: list[AffectedCodelist]
) -> str:
    """Render an operational overview grouped by each kind of known issue."""
    description_issues: dict[
        str, tuple[dict[str, str | bool], list[AffectedCodelist]]
    ] = {}
    moved_issues: dict[str, tuple[dict[str, object], list[AffectedCodelist]]] = {}

    for codelist in affected:
        for code, change in codelist.description_changes.items():
            description_issues.setdefault(code, (change, []))[1].append(codelist)
        for moved in codelist.moved_code_sets:
            title = str(moved["title"])
            moved_issues.setdefault(title, (moved, []))[1].append(codelist)

    users = sorted(
        (owner for owner in reports if owner.kind == "user"),
        key=lambda owner: (owner.name.lower(), owner.identifier),
    )
    organisations = sorted(
        (owner for owner in reports if owner.kind == "organisation"),
        key=lambda owner: (owner.name.lower(), owner.identifier),
    )
    lines = [
        "# ICD-10 codelist impact report",
        "",
        "## Summary",
        "",
        f"- Affected users: **{len(users)}**",
        f"- Affected organisations: **{len(organisations)}**",
        f"- Affected codelists: **{len(affected)}**",
        f"- Changed-description issues: **{len(description_issues)}**",
        f"- Moved-code issues: **{len(moved_issues)}**",
        "",
        "### Affected users",
        "",
        *[f"- {escape_markdown(owner.name)}: {len(reports[owner])}" for owner in users],
        "",
        "### Affected organisations",
        "",
        *[
            f"- {escape_markdown(owner.name)}: {len(reports[owner])}"
            for owner in organisations
        ],
        "",
        "## Changed code descriptions",
        "",
    ]

    if not description_issues:
        lines.extend(["No affected codelists.", ""])
    for code, (change, codelists) in sorted(description_issues.items()):
        lines.extend(
            [
                f"### {code_span(code)}",
                "",
                f"- NHS 2016: {escape_markdown(change['combined_2016'])}",
                f"- WHO 2019: {escape_markdown(change['who_2019'])}",
                f"- Affected codelists: **{len(codelists)}**",
                "",
                *_summary_codelist_lines(codelists),
                "",
            ]
        )

    lines.extend(["## Concepts with moved codes", ""])
    if not moved_issues:
        lines.extend(["No affected codelists.", ""])
    for title, (moved, codelists) in sorted(moved_issues.items()):
        nhs_codes = ", ".join(code_span(code) for code in moved["nhs2016"])
        who_codes = ", ".join(code_span(code) for code in moved["who2019"])
        lines.extend(
            [
                f"### {escape_markdown(title)}",
                "",
                escape_markdown(moved["comment"]),
                "",
                f"- NHS 2016 codes: {nhs_codes}",
                f"- WHO 2019 codes: {who_codes}",
                f"- Affected codelists: **{len(codelists)}**",
                "",
                *_summary_codelist_lines(codelists),
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def _summary_codelist_lines(codelists: list[AffectedCodelist]) -> list[str]:
    lines = []
    for codelist in sorted(codelists, key=lambda item: (item.name.lower(), item.slug)):
        url = f"{BASE_URL}{codelist.path()}"
        owner = codelist.user_id or codelist.organisation_id or ""
        owner_type = "user" if codelist.user_id else "organisation"
        lines.append(
            f"- [{escape_markdown(codelist.name)}]({url}) — "
            f"{owner_type} {code_span(owner)}"
        )
    return lines


def write_pdf(markdown: str, path: Path) -> None:
    """Render Markdown to a PDF using the chrome browser."""
    browser_path = shutil.which("google-chrome")
    if browser_path is None:
        raise RuntimeError("PDF generation requires Google Chrome")

    document = markdown2.markdown(markdown, safe_mode="escape")
    html_document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(path.stem)}</title>
  <style>{PDF_CSS}</style>
</head>
<body>{document}</body>
</html>
"""
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="icd10-report-") as temp_dir:
        temp_path = Path(temp_dir)
        html_path = temp_path / "report.html"
        html_path.write_text(html_document, encoding="utf-8")
        try:
            subprocess.run(
                [
                    browser_path,
                    "--headless",
                    "--disable-gpu",
                    "--no-pdf-header-footer",
                    f"--user-data-dir={temp_path / 'browser-profile'}",
                    f"--print-to-pdf={path}",
                    html_path.as_uri(),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError) as error:
            details = getattr(error, "stderr", "") or str(error)
            raise RuntimeError(f"Failed to generate PDF {path}: {details}") from error
