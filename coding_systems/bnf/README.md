BNF
---

BNF codes are used to identify anything that is prescribed in England (and maybe elsewhere).

For more details, see [our most popular blog post][0].

We obtain the data from the NHSBSA Open Data Portal (ODP). New releases are published monthly.
[The release page][1] displays each release for the current calendar year in the Data and Resources section.
The name of each release contains the date and version for that release, for example, "BNF Code Information - Current - June 2026 Version 90".
Each monthly release is published as a CSV file whose name includes the year, month and release version. For example, `bnf_code_current_202606_version_90.csv` corresponds to the June 2026 release of version 90.

Download the latest BNF release CSV and copy it to the BNF data folder on dokku3,
at `/var/lib/dokku/data/storage/opencodelists/data/bnf/`.

To import the data, run:

```sh
./manage.py import_coding_system_data bnf
/storage/data/bnf/<csvfile>
--release <release_name>
--valid-from <valid_from>
--import-ref <import_ref>
```

- `release_name` is the name of the release in `<version> (<date>)` format.
  - `<version>` is the release version number.
  - `<date>` is the release date in `YYYY-MM-DD` format. As the ODP filenames only include the year and month, use the first day of the month (for example, `2026-06-01`).
- `valid_from` is the date of the release in `YYYY-MM-DD` format.
  (It is *not* the date the data are imported into OpenCodelists.)
- `import_ref` is an optional reference for any other information. Include the name of the csv file.

For the example above (`bnf_code_current_202606_version_90.csv`),
the data should be imported with:

```sh
dokku run opencodelists python manage.py import_coding_system_data bnf
/storage/data/bnf/bnf_code_current_202606_version_90.csv
--release '90 (2026-06-01)'
--valid-from 2026-06-01
--import-ref bnf_code_current_202606_version_90.csv
```

After importing, restart the opencodelists app with:

```sh
dokku ps:restart opencodelists
```

[0]: https://www.bennett.ox.ac.uk/blog/2017/04/prescribing-data-bnf-codes/
[1]: https://opendata.nhsbsa.net/dataset/bnf-code-information-current-year
