"""Generate per-repository ICD-10 codelist review reports."""

import argparse
import base64
import html
import json
import re
import subprocess
import tempfile
from collections import defaultdict
from datetime import date
from pathlib import Path

import markdown2

from .common import (
    PORT_DIR,
    InputPaths,
    extract_icd10_codes,
    filter_cohortextractor_moved_codes,
    find_all_codes_in_github,
    get_actual_codes,
    get_project_type,
    load_changed_code_definitions,
    load_prefix_matching_details,
    load_prefix_matching_warnings,
    load_project_type_overrides,
    load_swapped_codes,
    load_usage_data,
    run_gh_command,
)


DEFAULT_REPORTS_DIR = PORT_DIR / "reports"
REQUIRED_INPUT_FILES = (
    "swapped_codes.json",
    "changed_code_definitions.json",
    "code_usage_combined_apcs.csv",
    "prefix_matching_repos.csv",
    "prefix_matching_details.json",
)
CHROME_COMMAND = "google-chrome"
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
a { color: #0967a8; text-decoration: underline; }
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

OPENSAFELY_CHAPTER_CODELIST_RE = re.compile(
    r"^opensafely-icd-10-chapter-([ivxlcdm]+)\.[^.]+$", re.IGNORECASE
)

MODIFIER_INTRO = (
    "The following codelist(s) contain an ICD-10 code but none of its immediate "
    "modifier children. These modifier codes were not supported in the previous "
    "OpenCodelists ICD-10 database, but are now available for selection. If you "
    "don't include these missing codes then your codelist may miss some events. "
    "You may want to use a newer version of the codelist that includes the "
    "modifiers."
)

MODIFIER_NB = (
    "**NB: This warning is only relevant when querying the primary and secondary "
    "diagnosis fields in the APCS admissions data. If you are using the all_diagnoses "
    "field, and the contains() or contains_any_of() functions, then this is not "
    'needed as these functions "prefix match".**'
)

DEFINITION_INTRO = (
    "The following codelist(s) have codes whose description in the 2016 release "
    "of ICD-10 (used in APCS admissions data) differs from the description in the "
    "2019 release (used in ONS deaths data). "
)

EHRQL_DEFINITION_INTRO = DEFINITION_INTRO + (
    "If you include these codes in your "
    "codelist they may not match the events you expect depending on which data "
    "source you are targeting. You should review the codes to decide whether they "
    "are appropriate for your purposes. More instructions on how to resolve this "
    "are [available here](https://opencodelists.org/docs/#if-a-code-has-conflicting-definitions)."
)

COHORTEXTRACTOR_DEFINITION_INTRO = DEFINITION_INTRO + (
    "A code may have represented a different condition depending on the data "
    "source queried. More information on conflicting definitions is "
    "[available here](https://opencodelists.org/docs/#if-a-code-has-conflicting-definitions)."
)

MOVED_CODE_INTRO = (
    "The following codelist(s) have codes that have changed between the 2016 "
    "release of ICD-10 (used in APCS admissions data) and the 2019 release (used "
    "in ONS deaths data). We have found that some of the codelists in your project "
    "contain one of these codes from one release, but not the equivalent code from "
    "the other release. "
)

EHRQL_MOVED_CODE_INTRO = MOVED_CODE_INTRO + (
    "By not including the missing code, you may miss events "
    "depending on which data table you are targeting. You may want to use a newer "
    "version of the codelist that includes both codes."
)

COHORTEXTRACTOR_MOVED_CODE_INTRO = MOVED_CODE_INTRO + (
    "As a result, the original analysis may not have matched some events, depending "
    "on which data table you queried"
)

X_PADDING_INTRO = (
    "The following codelist(s) contain 3 character ICD-10 codes. NHS hospital "
    "admission data pads 3 character codes with an 'X' to make them 4 characters. "
    "If you don't include the 'X' padded version of the code then your codelist may "
    "miss some events. OpenCodelists does not yet support this, but the following "
    "workaround can be added to your ehrQL code:"
)

X_PADDING_SNIPPET = """```python
# Assume we have a codelist called 'my_codelist' that contains 3 character ICD-10 codes
# This snippet will add the 'X' padded version of any 3 character codes to the codelist
my_codelist = my_codelist + [code + 'X' for code in my_codelist if len(code) == 3]
```"""

X_PADDING_NB = (
    "**NB: This workaround is only needed when querying the primary and secondary "
    "diagnosis fields in the APCS admissions data. If you are using the all_diagnoses "
    "field, and the contains() or contains_any_of() functions, then this is not "
    'needed as these functions "prefix match".**'
)


def count(warning, key):
    try:
        return int(warning[key])
    except (KeyError, TypeError, ValueError):
        return 0


def usage_total(usage_totals, code, field="apcs_all_count"):
    return usage_totals.get(code, {}).get((field, "TOTAL"), 0)


def minimal_prefixes(codes):
    """Remove codes already covered by a shorter code in the codelist."""
    return {
        code
        for code in codes
        if not any(code != other and code.startswith(other) for other in codes)
    }


def codelist_usage_total(
    usage_totals, codes, prefix_matching=False, field="apcs_all_count"
):
    """Sum APCS usage using ehrQL or Cohort Extractor matching semantics."""
    if prefix_matching:
        prefixes = minimal_prefixes(codes)
        return sum(
            usage_total(usage_totals, code, field)
            for code in usage_totals
            if any(code.startswith(prefix) for prefix in prefixes)
        )

    stored_codes = {f"{code}X" if len(code) == 3 else code for code in codes}
    return sum(usage_total(usage_totals, code, field) for code in stored_codes)


def format_ehrql_counts(primary, all_diagnoses):
    return (
        f"{primary:,} events in `primary_diagnosis` and "
        f"{all_diagnoses:,} events in `all_diagnoses`"
    )


def codelist_name(codelist_id):
    parts = codelist_id.strip("/").split("/")
    return parts[-2] if len(parts) >= 2 else codelist_id


def codelist_url(codelist_id):
    return f"https://www.opencodelists.org/codelist{codelist_id}"


def github_file_name(path):
    return Path(path).stem.replace("_", " ").replace("-", " ")


def opensafely_chapter(path):
    """Return the Roman-numeral chapter for an OpenSAFELY chapter codelist."""
    match = OPENSAFELY_CHAPTER_CODELIST_RE.fullmatch(Path(path).name)
    return match.group(1).lower() if match else None


def format_code_list(codes):
    return ", ".join(f"`{code}`" for code in sorted(codes))


def convert_markdown_to_pdf(markdown_path):
    pdf_path = markdown_path.with_suffix(".pdf")
    print(f"    Creating PDF {pdf_path}...", end="", flush=True)
    markdown = markdown_path.read_text()
    document = markdown2.markdown(
        markdown,
        safe_mode="escape",
        extras=["fenced-code-blocks", "code-friendly"],
    )
    html_document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(markdown_path.stem)}</title>
  <style>{PDF_CSS}</style>
</head>
<body>{document}</body>
</html>
"""
    try:
        with tempfile.TemporaryDirectory(prefix="icd10-report-") as temp_dir:
            html_path = Path(temp_dir) / "report.html"
            html_path.write_text(html_document)
            subprocess.run(
                [
                    CHROME_COMMAND,
                    "--headless",
                    "--disable-gpu",
                    "--no-sandbox",
                    f"--print-to-pdf={pdf_path}",
                    html_path.as_uri(),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
        print(" done")
    except (OSError, subprocess.CalledProcessError, UnicodeError) as error:
        print(f" failed\nWARNING: Could not create PDF for {markdown_path}: {error}")
        try:
            pdf_path.unlink()
        except OSError:
            pass

    return pdf_path


def generate_repo_emails(
    all_results,
    codes,
    groups,
    usage_totals,
    prefix_warnings,
    changed_definitions=None,
    project_types=None,
    prefix_details=None,
    generated_on=None,
    reports_dir=DEFAULT_REPORTS_DIR,
):
    """Generate one template-based Markdown report per affected repository."""
    del codes  # Descriptions come from the structured moved/definition inputs.
    changed_definitions = changed_definitions or {}
    project_types = project_types or {}
    prefix_details = prefix_details or {}
    generated_on = generated_on or date.today().isoformat()

    def project_type_for(repo):
        repo_name = repo.removeprefix("opensafely/")
        return (
            project_types.get(repo)
            or project_types.get(repo_name)
            or project_types.get(f"opensafely/{repo_name}")
        )

    repo_file_matches = defaultdict(lambda: defaultdict(list))
    for code, repo_results in all_results.items():
        for repo, matches in repo_results.items():
            if project_type_for(repo) == "ignore":
                continue
            for match in matches:
                chapter = opensafely_chapter(match["path"])
                if project_type_for(repo) == "cohortextractor" and chapter not in (
                    None,
                    "i",
                ):
                    continue
                if chapter == "i" and code == "A925":
                    continue
                repo_file_matches[repo][match["path"]].append(
                    {"code": code, "line": match["line_text"]}
                )

    reports_dir.mkdir(parents=True, exist_ok=True)
    for old_file in reports_dir.rglob("*.md"):
        try:
            old_file.unlink()
        except OSError:
            pass
    for old_file in reports_dir.rglob("*.pdf"):
        try:
            old_file.unlink()
        except OSError:
            pass

    def format_repo_report(repo, files_by_path):
        repo_name = repo.removeprefix("opensafely/")
        project_type = project_type_for(repo)
        warnings = prefix_warnings.get(repo_name, []) if project_type == "ehrql" else []

        x_warnings = [
            warning
            for warning in warnings
            if count(warning, "x_padded") > count(warning, "current")
        ]
        modifier_warnings = [
            warning
            for warning in warnings
            if count(warning, "with_prefix") > count(warning, "x_padded")
        ]

        default_branch = None
        file_cache = {}

        def get_default_branch():
            nonlocal default_branch
            if default_branch is not None:
                return default_branch
            success, output = run_gh_command(["api", f"repos/opensafely/{repo_name}"])
            default_branch = "main"
            if success and output:
                try:
                    default_branch = json.loads(output).get("default_branch") or "main"
                except json.JSONDecodeError:
                    pass
            return default_branch

        def get_file_codes(path):
            if path in file_cache:
                return file_cache[path]
            print(f"    Loading {path}...", end="", flush=True)
            branch = get_default_branch()
            success, output = run_gh_command(
                ["api", f"repos/opensafely/{repo_name}/contents/{path}?ref={branch}"]
            )
            contents = ""
            if success and output:
                try:
                    payload = json.loads(output)
                    if payload.get("content") and payload.get("encoding") == "base64":
                        contents = base64.b64decode(payload["content"]).decode(
                            "utf-8", errors="replace"
                        )
                except (json.JSONDecodeError, ValueError, TypeError):
                    pass
            file_cache[path] = extract_icd10_codes(contents)
            if success:
                print(f" {len(file_cache[path])} ICD-10 codes")
            else:
                print(" unavailable; using matched codes only")
            return file_cache[path]

        def github_file_url(path):
            return (
                f"https://github.com/opensafely/{repo_name}/blob/"
                f"{get_default_branch()}/{path}"
            )

        changed_by_file = []
        moved_by_file = []
        prefix_matching = project_type == "cohortextractor"
        for path, matches in sorted(files_by_path.items()):
            match_codes = {match["code"] for match in matches}
            file_codes = get_file_codes(path) | match_codes
            current_usage = codelist_usage_total(
                usage_totals, file_codes, prefix_matching=prefix_matching
            )
            current_primary_usage = codelist_usage_total(
                usage_totals, file_codes, field="apcs_primary_count"
            )
            changed_code_set = match_codes & set(changed_definitions)
            changed_codes = sorted(changed_code_set)
            if project_type == "cohortextractor":
                changed_codes = [
                    code
                    for code in changed_codes
                    if codelist_usage_total(
                        usage_totals,
                        file_codes - {code},
                        prefix_matching=True,
                    )
                    != current_usage
                ]
                changed_code_set = set(changed_codes)
            if changed_codes:
                changed_by_file.append(
                    {
                        "path": path,
                        "codes": changed_codes,
                        "current": current_usage,
                        "current_primary": current_primary_usage,
                        "without_changed": codelist_usage_total(
                            usage_totals,
                            file_codes - changed_code_set,
                            prefix_matching=prefix_matching,
                        ),
                        "without_changed_primary": codelist_usage_total(
                            usage_totals,
                            file_codes - changed_code_set,
                            field="apcs_primary_count",
                        ),
                    }
                )

            group_findings = []
            for group in groups:
                searched_codes = set(group.get("codes", []))
                if not searched_codes & match_codes:
                    continue
                equivalent_codes = (
                    searched_codes
                    | set(get_actual_codes(group, searched_codes))
                    | set(group.get("related_codes", []))
                )
                found_codes = equivalent_codes & file_codes
                missing_codes = equivalent_codes - found_codes
                if not missing_codes:
                    continue
                group_findings.append(
                    {
                        "description": group.get("description", "Affected codes"),
                        "found": sorted(found_codes),
                        "missing": sorted(missing_codes),
                        "current": current_usage,
                        "current_primary": current_primary_usage,
                        "would": codelist_usage_total(
                            usage_totals,
                            file_codes | missing_codes,
                            prefix_matching=prefix_matching,
                        ),
                        "would_primary": codelist_usage_total(
                            usage_totals,
                            file_codes | missing_codes,
                            field="apcs_primary_count",
                        ),
                    }
                )
            if group_findings:
                moved_by_file.append((path, group_findings))

        sections = []
        x_padding_sections = []

        if modifier_warnings:
            lines = [
                "## Action recommended: modifier codes may be missing",
                "",
                MODIFIER_INTRO,
                "",
                MODIFIER_NB,
                "",
                "Event counts in this section are 2024-25 APCS totals.",
                "",
            ]
            for warning in modifier_warnings:
                codelist = warning["codelist"]
                details = prefix_details.get(codelist, {})
                modifier_codes = details.get("modifier_codes", [])
                lines.extend(
                    [
                        f"[{codelist_name(codelist)}]({codelist_url(codelist)})",
                        "",
                        f"- Potentially missing modifier codes: {format_code_list(modifier_codes)}",
                        "- Codelist currently matches: "
                        + format_ehrql_counts(
                            count(warning, "x_padded"),
                            count(details, "with_x_padding_all"),
                        ),
                        "- Codelist would match: "
                        + format_ehrql_counts(
                            count(warning, "with_prefix"),
                            count(details, "with_prefix_matching_all"),
                        )
                        + " if missing modifier codes were included",
                        "",
                    ]
                )
            sections.append(lines)

        if changed_by_file:
            lines = [
                (
                    "## For information: code descriptions differed"
                    if project_type == "cohortextractor"
                    else "## Action required: code descriptions differ"
                ),
                "",
                (
                    COHORTEXTRACTOR_DEFINITION_INTRO
                    if project_type == "cohortextractor"
                    else EHRQL_DEFINITION_INTRO
                ),
                "",
                "Event counts in this section are all-years APCS totals.",
                "",
            ]
            for finding in changed_by_file:
                lines.extend(
                    [
                        f"[{github_file_name(finding['path'])}]"
                        f"({github_file_url(finding['path'])})",
                        "",
                    ]
                )
                for code in finding["codes"]:
                    definitions = changed_definitions[code]
                    lines.extend(
                        [
                            f"- **`{code}`:**",
                            f"  - NHS 2016 definition: {definitions['2016']}",
                            f"  - WHO 2019 definition: {definitions['2019']}",
                        ]
                    )
                if project_type == "ehrql":
                    current = format_ehrql_counts(
                        finding["current_primary"], finding["current"]
                    )
                    without_changed = format_ehrql_counts(
                        finding["without_changed_primary"],
                        finding["without_changed"],
                    )
                else:
                    current = f"{finding['current']:,} APCS events"
                    without_changed = f"{finding['without_changed']:,} APCS events"
                lines.extend(
                    [
                        (
                            f"- Events matched by the codelist: {current}"
                            if project_type == "cohortextractor"
                            else f"- Codelist currently matches: {current}"
                        ),
                        (
                            f"- Codelist would have matched: {without_changed} if all "
                            "codes with differing descriptions were removed"
                            if project_type == "cohortextractor"
                            else f"- Codelist would match: {without_changed} if all "
                            "codes with differing descriptions were removed"
                        ),
                        "",
                    ]
                )
            sections.append(lines)

        if moved_by_file:
            lines = [
                (
                    "## For information: codes may have been missing"
                    if project_type == "cohortextractor"
                    else "## Action recommended: codes may be missing"
                ),
                "",
                (
                    COHORTEXTRACTOR_MOVED_CODE_INTRO
                    if project_type == "cohortextractor"
                    else EHRQL_MOVED_CODE_INTRO
                ),
                "",
                "Event counts in this section are all-years APCS totals.",
                "",
            ]
            for path, findings in moved_by_file:
                lines.extend(
                    [
                        f"[{github_file_name(path)}]({github_file_url(path)})",
                        "",
                    ]
                )
                for finding in findings:
                    if project_type == "ehrql":
                        current = format_ehrql_counts(
                            finding["current_primary"], finding["current"]
                        )
                        would = format_ehrql_counts(
                            finding["would_primary"], finding["would"]
                        )
                    else:
                        current = f"{finding['current']:,} APCS events"
                        would = f"{finding['would']:,} APCS events"
                    lines.extend(
                        [
                            f"- **{finding['description']}:** Equivalent codes differ between the NHS 2016 and WHO 2019 releases.",
                            "  - Codes found in this codelist: "
                            f"{format_code_list(finding['found'])}",
                            "  - Codes potentially missing from this codelist: "
                            f"{format_code_list(finding['missing'])}",
                            f"  - Codelist currently matches: {current}",
                            f"  - Codelist would match: {would} if missing codes were included",
                        ]
                    )
                lines.append("")
            sections.append(lines)

        if x_warnings:
            lines = [
                "## Action recommended: missing 'X' padded codes",
                "",
                X_PADDING_INTRO,
                "",
                "Event counts in this section are 2024-25 APCS totals.",
                "",
                X_PADDING_SNIPPET,
                "",
                X_PADDING_NB,
                "",
            ]
            for warning in x_warnings:
                codelist = warning["codelist"]
                details = prefix_details.get(codelist, {})
                x_codes = details.get("x_padded_codes", [])
                lines.extend(
                    [
                        f"[{codelist_name(codelist)}]({codelist_url(codelist)})",
                        "",
                        f"- Codes that should be 'X' padded: {format_code_list(x_codes)}",
                        "- Codelist currently matches: "
                        + format_ehrql_counts(
                            count(warning, "current"),
                            count(details, "baseline_all"),
                        ),
                        "- Codelist would match: "
                        + format_ehrql_counts(
                            count(warning, "x_padded"),
                            count(details, "with_x_padding_all"),
                        )
                        + " if 'X' padded codes were included",
                        "",
                    ]
                )
            x_padding_sections.append(lines)

        def render_report(report_sections):
            if not report_sections:
                return None

            lines = [
                "# ICD-10 codelists that require review",
                "",
                "Following the new ICD-10 OpenSAFELY release on OpenCodelists, "
                f"we've identified that the project, [{repo_name}]"
                f"(https://github.com/opensafely/{repo_name}), is using ICD-10 "
                "codelists that should be reviewed.",
                "",
                "**This report only lists the codelists we've identified as "
                "requiring review.** It explains why each has been flagged and "
                "provides links to review the relevant codelist or source file.",
                "",
            ]
            for section in report_sections:
                lines.extend(section)
            return "\n".join(lines).rstrip() + "\n"

        if sections:
            return render_report([*sections, *x_padding_sections]), None
        return None, render_report(x_padding_sections)

    prefix_repos = {
        repo for repo in prefix_warnings if project_type_for(repo) == "ehrql"
    }
    all_repos = set(repo_file_matches) | prefix_repos
    sorted_repos = sorted(all_repos)
    print(f"\nGenerating reports for {len(sorted_repos)} repositories...")
    for repo_index, repo in enumerate(sorted_repos, start=1):
        repo_name = repo.removeprefix("opensafely/")
        project_type = project_type_for(repo)
        files_by_path = repo_file_matches.get(repo, {})
        print(
            f"  [{repo_index}/{len(sorted_repos)}] {repo_name} "
            f"({project_type or 'unknown'}, {len(files_by_path)} files)"
        )
        report, x_padding_report = format_repo_report(repo, files_by_path)
        reports_to_write = []
        if report is not None:
            output_dir = reports_dir / project_type if project_type else reports_dir
            reports_to_write.append((output_dir, report))
        if x_padding_report is not None:
            reports_to_write.append((reports_dir / "ehrql-x-padding", x_padding_report))
        if not reports_to_write:
            print("    No report findings remain")

        for output_dir, content in reports_to_write:
            output_path = output_dir / f"{repo_name}.md"
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(content)
                print(f"    Wrote {output_path}")
                convert_markdown_to_pdf(output_path)
            except OSError as error:
                print(f"WARNING: Could not write report for {repo}: {error}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=PORT_DIR / "data",
        help="Directory containing the private report input files",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=DEFAULT_REPORTS_DIR,
        help="Directory in which generated Markdown and PDF reports are written",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Discard the GitHub search cache and repeat every code search",
    )
    args = parser.parse_args(argv)
    input_paths = InputPaths(args.data_dir)

    missing_files = [
        filename
        for filename in REQUIRED_INPUT_FILES
        if not input_paths.file(filename).is_file()
    ]
    if missing_files:
        parser.error(
            "Missing required input files:\n  "
            + "\n  ".join(str(input_paths.file(name)) for name in missing_files)
        )

    success, error = run_gh_command(["--version"])
    if not success:
        parser.error(f"Could not run gh CLI: {error}")

    moved_codes, groups = load_swapped_codes(input_paths)
    changed_definitions = load_changed_code_definitions(input_paths)
    if not moved_codes and not changed_definitions:
        parser.error("No moved codes or changed definitions were loaded")

    codes = dict(moved_codes)
    codes.update(
        {code: definitions["2019"] for code, definitions in changed_definitions.items()}
    )

    all_results = find_all_codes_in_github(
        set(codes), args.force, input_paths=input_paths
    )
    overrides = load_project_type_overrides(input_paths)
    all_results, project_types = filter_cohortextractor_moved_codes(
        all_results, groups, overrides
    )
    usage_totals, _ = load_usage_data("apcs", input_paths)
    prefix_warnings = load_prefix_matching_warnings(input_paths)
    prefix_details = load_prefix_matching_details(input_paths)

    for repo_name in prefix_warnings:
        repo = f"opensafely/{repo_name}"
        if not project_types.get(repo):
            project_types[repo] = get_project_type(repo, overrides) or "ehrql"

    unknown_repos = sorted(
        repo.removeprefix("opensafely/")
        for repo, project_type in project_types.items()
        if project_type is None
    )
    if unknown_repos:
        print(
            "\nUncategorised repositories (add these to "
            f"{input_paths.file('project_type_overrides.json')}):"
        )
        for repo in unknown_repos:
            print(f'  "{repo}": "ehrql"')

    generate_repo_emails(
        all_results,
        codes,
        groups,
        usage_totals,
        prefix_warnings,
        changed_definitions,
        project_types,
        prefix_details,
        reports_dir=args.reports_dir,
    )


if __name__ == "__main__":
    main()
