# ICD-10 project report generator

This standalone tool identifies OpenSAFELY repositories whose ICD-10 codelists may be affected by differences between ICD-10 releases. It produces Markdown and PDF reports for ehrQL and Cohort Extractor projects.

## Requirements

- GitHub CLI (`gh`)
- Google Chrome available as `google-chrome` for PDF output. (NB means this needs to run locally will not work on production server)

Authenticate GitHub if necessary:

```sh
gh auth login
```

## Input data

Input files belong in:

```text
scripts/icd10_project_reports/data/
```

The following required files contain sensitive count data that shouldn't be committed and are ignored by Git. Instructions to create these files, for users with the appropriate permissions, are available [here](https://github.com/opensafely/tpp-code-counts/tree/main/reporting#recommended-execution-order). Copy the required files into the data directory before running the tool:

- code_usage_combined_apcs.csv
- prefix_matching_repos.csv
- prefix_matching_details.json

## Running

From the OpenCodelists repository root:

```sh
uv run python scripts/generate_icd10_project_reports.py
```

To use data or report directories elsewhere:

```sh
uv run python scripts/generate_icd10_project_reports.py \
  --data-dir /path/to/data \
  --reports-dir /path/to/reports
```

By default GitHub searches are cached because they take so long to run. Use --force to discard the GitHub search cache and repeat every code search:

```sh
uv run python scripts/generate_icd10_project_reports.py --force
```

## Outputs

The default output directory is:

```sh
scripts/icd10_project_reports/reports/
```

It is ignored by Git. Reports are split into:

- ehrql/ (ehrQL projects affected by the ICD-10 changes - includes info about x-padded codes if applicable)
- ehrql-x-padding/ (ehrQL projects not affected by the ICD-10 changes but which need the x-padding info)
- cohortextractor/ (cohortextractor projects affected by the ICD-10 changes)

Each report is written as Markdown and PDF.

## Tests

```sh
just test-py-nocov scripts/tests/test_icd10_project_reports.py
```
