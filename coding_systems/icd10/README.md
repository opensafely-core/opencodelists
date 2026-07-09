# ICD-10

ICD-10 imports in OpenCodelists are a combined release built from:

- WHO ICD-10 2016 ClaML
- WHO ICD-10 2019 ClaML
- NHS Class Browser scraped 2016 data (converted to ClaML)

The importer then loads two editions (`2016` and `2019`) into the imported database.

## Current import workflow

Run:

```bash
# Local development
just manage import_latest_data icd10 ./coding_systems/icd10/data

# Production
dokku run opencodelists python manage.py import_latest_data icd10 /storage/data/icd10/
dokku ps:restart opencodelists
```

This command does all of the following automatically:

1. Downloads WHO ClaML ZIPs for 2016 and 2019.
2. Scrapes NHS ICD-10 Class Browser data and converts it to ClaML.
3. Builds a combined ZIP containing all three XML files.
4. Computes a content digest and aborts if the same content has already been imported.
5. Parses all sources and builds a combined 2016 record set.
6. Runs known-difference checks:
   - WHO 2016 vs scraped 2016
   - combined 2016 vs WHO 2019
7. Imports the coding system release.

## Where assumptions are defined

Expected differences and inclusion/exclusion decisions are defined in:

- `coding_systems/icd10/known_diffs.py`

If import fails with unexpected differences, update this file with the new expected diff decisions, then rerun the import.

## Release metadata behavior

For ICD-10, release metadata is generated automatically by the downloader:

- `release_name`: `combined_<timestamp>_<content_digest>`
- `valid_from`: current date at import time
- `filename`: `combined_<timestamp>.zip`

## Output cache directory

The `release_dir` you pass to `import_latest_data` is used to cache:

- downloaded WHO ZIPs
- scraped NHS ZIP/XML artifacts
- generated combined ZIP used for import
