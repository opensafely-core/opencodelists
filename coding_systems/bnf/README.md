# BNF

BNF codes are used to identify anything that is prescribed in England (and maybe elsewhere).

For more details, see [our most popular blog post](https://www.bennett.ox.ac.uk/blog/2017/04/prescribing-data-bnf-codes/).

We obtain the data from the NHSBSA Open Data Portal (ODP). New releases are published monthly. [The release page](https://opendata.nhsbsa.net/dataset/bnf-code-information-current-year) displays each release for the current calendar year in the Data and Resources section. The name of each release contains the date and version for that release, for example, "BNF Code Information - Current - June 2026 Version 90". Each monthly release is published as a CSV file whose name includes the year, month and release version. For example, `bnf_code_current_202606_version_90.csv` corresponds to the June 2026 release of version 90.

Download the latest BNF release CSV and copy it to the BNF data folder on dokku3: `/coding_system_data_block_storage/data/bnf/`.

To import the data, run:

```sh
dokku run opencodelists python manage.py import_coding_system_data bnf \
  CSV_FILE \
  --release RELEASE_NAME \
  --valid-from VALID_FROM \
  --import-ref IMPORT_REF
```

- `CSV_FILE` is the path to the downloaded CSV file in `/coding_system_data_block_storage/data/bnf/`.
- `RELEASE_NAME` identifies the release in `VERSION (DATE)` format.
  - `VERSION` is the release version number
  - `DATE` is the release date in `YYYY-MM-DD` format.
  - As the ODP filenames include only the year and month, use the first day of the month (for example, `2026-06-01`).
- `VALID_FROM` is the release date in `YYYY-MM-DD` format, not the date the data are imported into OpenCodelists.
- `IMPORT_REF` is an optional reference for additional information. Include the CSV filename.

For the example file `bnf_code_current_202606_version_90.csv`, use:

```sh
dokku run opencodelists python manage.py import_coding_system_data bnf \
  /coding_system_data_block_storage/data/bnf/bnf_code_current_202606_version_90.csv \
  --release '90 (2026-06-01)' \
  --valid-from 2026-06-01 \
  --import-ref bnf_code_current_202606_version_90.csv
```

After importing, restart the OpenCodelists app:

```sh
dokku ps:restart opencodelists
```
