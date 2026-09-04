# ICD-10 project report generator

This standalone tool identifies OpenSAFELY repositories whose ICD-10 codelists
may be affected by differences between ICD-10 releases. It produces Markdown
and PDF reports for ehrQL and Cohort Extractor projects.

It is deliberately independent of the OpenCodelists Django application and its
databases. The static ICD-10 change definitions are version controlled with the
tool. Sensitive count and matching data is copied into this checkout only when
a report run is needed and must never be committed.

## Requirements

- The OpenCodelists Python 3.12 development environment.
- GitHub CLI (`gh`), authenticated for access to OpenSAFELY repositories.
- Google Chrome available as `google-chrome` for PDF output.

Authenticate GitHub if necessary:

```sh
gh auth login
```

## Input data

Input files belong in:

```text
scripts/icd10_project_reports/data/
```

The following static definition files are version controlled and should be
updated only when a newer ICD-10 release introduces additional changes:

- swapped_codes.json
- changed_code_definitions.json

The following required runtime files contain sensitive or derived analysis data
and are ignored by Git. Copy them into the directory before running the tool:

- code_usage_combined_apcs.csv
- prefix_matching_repos.csv
- prefix_matching_details.json

Optional ignored runtime files:

- project_type_overrides.json: manual ehrql, cohortextractor, or ignore
  classifications keyed by repository name.
- github_code_search_cache.json: cached GitHub code-search results. The tool
  creates or updates this file; copying an existing cache avoids repeating
  searches and reduces the chance of hitting GitHub API rate limits.

The files retain the same formats produced by the reporting pipeline in
tpp-code-counts.

## Running

From the OpenCodelists repository root:

```sh
uv run python scripts/generate_icd10_project_reports.py
```

To use data or report directories elsewhere:

```sh
uv run python scripts/generate_icd10_project_reports.py \
  --data-dir /path/to/private/data \
  --reports-dir /path/to/reports
```

Use --force to discard the GitHub search cache and repeat every code search:

```sh
uv run python scripts/generate_icd10_project_reports.py --force
```

GitHub is still queried for repository classifications, current codelist
contents, and default branches. Progress is printed for these slower operations.

## Outputs

The default output directory is:

```sh
scripts/icd10_project_reports/reports/
```

It is ignored by Git. Reports are split into:

- ehrql/
- ehrql-x-padding/
- cohortextractor/

Each report is written as Markdown and PDF. Existing Markdown and PDF files
beneath the selected reports directory are removed before a run, so that
directory should be dedicated to this tool.

## Tests

Run the standalone test module with:

```sh
just test-py-nocov scripts/tests/test_icd10_project_reports.py
```

The tests validate the committed static definitions and use synthetic private
inputs in temporary directories. They do not require or expose private runtime
data.
