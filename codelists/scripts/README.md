# Bulk import codelists from a file

`codelists/scripts/bulk_import_codelists.py` reads a file and creates new
codelists/codelist versions. By default, new versions are created as "under review";
pass `--force-publish` to publish immediately.

This script is intended to be run on a local machine, and will use the OpenCodelists
API to create the new codelist versions.

## Running the script

```
usage: bulk_import_codelists.py [-h] [--force-new-version] [--force-description]
                                [--force-name] [--force-publish] [--force-slug]
                                [--ignore-unfound-codes] [--live-run]
                                [--host HOST]
                                file_path config_file

positional arguments:
  file_path             Path/to/file
  config_file           Path/to/config/json/file

options:
  -h, --help            show this help message and exit
  --force-new-version, -f
                        Always create a new version, even if a version with
                        identical codes already exists.
  --force-description   Always update the description, even if it already
                        exists.
  --force-name          Always update the name, even if it already exists.
  --force-publish       Auto-publish new versions rather than leaving them
                        under review.
  --force-slug          Use the provided slug for new codelists instead of
                        generating one (requires a `codelist_new_slug`
                        column).
  --ignore-unfound-codes
                        Ignore codes that are not found in the coding system.
                        Useful for combined refsets that mix clinical and
                        medication codes; ignored codes are appended to the
                        methodology for reference.
  --live-run            Run this command for real; if not specified, this will be a
                        dry run that reports codelists/versions that will be
                        created but does not actually do anything.
  --host HOST           Host to use for API calls; https://www.opencodelists.org for
                        live prod run
```

Run with:
```sh
API_TOKEN=###
python codelists/scripts/ \bulk_import_codelists.py
    <path/to/file> \
    <path/to/config/json> \
    --host \ # run on the specified host; defaults to localhost:7000
    --force-new-version -f \ # to force a new version, even if there are no changes
    --live-run \ # run for real; if not set, just reports what would be done
```

Always run without the `--live-run` flag first. This will tell you if the script will
create a new codelist or a new version for each codelist in the file; confirm
that for any codelists that already exist, it reports that they will create new
*versions*.

To test with a local server, obtain a copy of the prod database and the relevant coding
system dbs, create an API token for the local user, run `just run` and then run
the script, using `--host http://localhost:7000`.

**NOTE:** when running on prod use --host https://www.opencodelists.org;
if run with https://opencodelists.org, the redirect to www will make the API calls
return 405s.

## Create API token

Create an API token via the django admin interface at {host}/admin. Alternatively,
create a token on the server (via the django shell) with:
```python
from rest_framework.authtoken.models import Token

user = User.objects.get(username=...)
token = Token.objects.create(user=user)
print(token.key)
```

NOTE: the token user must be a member of the relevant organisation on OpenCodelists.

## File format

Provide a path to an xlsx or tab/comma-delimited file (.txt files must state `delimiter` in config), which should contain at least one sheet, with at least columns (these can be aliased using the [config](#config)):
 - coding_system
 - codelist_name
 - code
 - term (only required if file includes dm+d codelists)
 - codelist_new_slug (optional; required only when using `--force-slug`)

The `coding_system` column may be omitted when the config specifies only a single coding system.

Optionally, a codelist_description field may be provided either to be used verbatim or with a template string specified in the [config](#config).

 Each row represents one code in one codelist version, e.g. the following represents
 one SNOMED-CT codelist and one dm+d codelist, each with 3 codes.

 coding_system | codelist_name | code
 --------------|---------------|-----
 snomedct      | Asthma        | 1234
 snomedct      | Asthma        | 2345
 snomedct      | Asthma        | 3456
 dmd           | Paracetemol   | ABCD
 dmd           | Paracetemol   | BCDE
 dmd           | Paracetemol   | CDEF

Note the columns names, coding system refs and codelist names can be aliased
in the config file, see below.

## Config

Provide a config file in json format

### Required keys
- **organisation** (Organisation slug)
- **sheet** (name of the sheet in the workbook that contains the list of codes)
- **coding_systems** (for each coding system value present in the workbook,
  the id of the coding system in OpenCodelists and the database alias of the
  release to be used for the new codelist. In the example below, the coding
  system column in the xlsx file  contains values "SNOMED CT" and "dm+d")

### Optional keys:
- **tag** (optional tag for the codelist versions)
- **column_aliases** (optional aliases for column names. We expect columns named
  coding_system, codelist_name, code, term (optional); column aliases is a dict
  mapping one or more of these column names to the actual name in the xlsx file.)
- **codelist_name_aliases** (in case the the name in OpenCodelists doesn't exactly
  match the value in the codelist_name column). This is a dict mapping from the
  name in the xlsx file (key) to name in OpenCodelists (value). It can also be
  used with the `limit_to_named_codelists` flag to specify updates for only a
  subset of codelists in the xlsx file.
- **limit_to_named_codelists**: boolean, defaults to False; only import update for
  codelists named in codelist_name_aliases
- **description_template**: template string for interpolation of
  `codelist_description` field in codelist descriptions (use standard `%` string
  formatting, e.g. `"Imported %s"`).
- **delimiter**: delimiter to use when reading `.txt` files.

### example_config.json:
```json
{
    "organisation": "pincer",
    "sheet": "SCT codeclusters",
    "coding_systems": {
        "SNOMED CT": {
            "id": "snomedct",
            "release": "snomedct_3600_20230419"
        },
        "dm+d": {
            "id": "dmd",
            "release": "dmd_2023-530_20230522"
        }
    },
    "tag": "v2.0",
    "column_aliases": {
        "coding_system": "Coding_scheme",
        "codelist_name": "Cluster_description",
        "code": "SNOMED code",
        "term": "SNOMED_Description",
    },
    "codelist_name_aliases": {
        "Loop diuretics": "Loop diuretics Rx",
        "Lithium medication": "Lithium Rx",
        "Methrotrexate": "Methotrexate Rx",
        "NSAID medication": "oral NSAID Rx",
        "Non Aspirin antiplatelet": "Antiplatelet Rx without aspirin Rx",
        "Non Selective Beta Blockers": "Non cardio-selective beta-blocker Rx",
        "Aspirin & other antiplatelets": "aspirin + other antiplatelet Rx",
        "PPIs and H2 blockers": "Ulcer healing drugs: PPI & H2 blockers Rx"
    },
    "limit_to_named_codelists": false
}
```

## Source-specific notes

### NHS Digital Primary Care Domain Refsets and NHS Drug Refsets

There are just commands to update the NHS PCD refsets:
```sh
just update-pcd-refsets
just update-drug-refsets
```
Please see `codelists/scripts/update_nhs_refsets.py` for more details.

#### Handling Errors

The API may return HTTP 5xx errors for certain resets,
this is usually because of codes that are present in the refset which are not in the SNOMED CT Clincal edition.
These are usually drug codes that are only present in the UK Drug Extension,
which is not loaded into the "SNOMED CT" coding system on OpenCodelists.

For the affected refsets, you will need to manually remove these codes,
import them as new versions,
and note their removal in the Description of the Codelist on OpenCodelists.

You may find the problematic codes by uploading a subset of the combined refset file
containing only the refset of interest as a new codelist in your own account
which will show the codes causing the errors.
