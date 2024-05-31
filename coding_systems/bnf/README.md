BNF
---

BNF codes are used to identify anything that is prescribed in England (and maybe elsewhere).

For more details, see [our most popular blog post][0].

We obtain the raw data from [the BSA][1].
New releases are published annually, sometimes with unannounced mid-year updates.
The release page will display the current release number for the year as of 1st Jan (e.g. "01-01-2022: 82");
updates are identified by the date in the downloaded filename.

Download the latest release, which will be a zipfile named something like `20220701_1656687539491_BNF_Code_Information.zip`.
Add this to the BNF data folder on dokku3, at `/var/lib/dokku/data/storage/opencodelists/data/bnf/`.

To import the data, run:

```sh
./manage.py bnf
path/to/zip/file/in/dokku/app
--release <release_name> --valid-from YYYY-MM-DD --import-ref <ref>
```

- `release` is a short label for this coding system release - the official version number as described above plus the date of any update.
- `valid-from` is the date that this release is valid from (NOT the date it is being imported into OpenCodelists), in YYYY-MM-DD format.
- `import-ref` is an optional long-form reference field for any other potential references or comments on this import if desired. Include at least the full downloaded zipfile here.

For the example above (`20220701_1656687539491_BNF_Code_Information.zip`),
the data should be imported with:

```sh
dokku run opencodelists python manage.py import_coding_system_data bnf
/storage/data/bnf/20220701_1656687539491_BNF_Code_Information.zip
--release '82 (2022-07-01)'
--valid-from 2022-07-01
--import-ref 20220701_1656687539491_BNF_Code_Information.zip
```

After importing, restart the opencodelists app with:

```sh
dokku ps:restart opencodelists
```

[0]: https://www.bennett.ox.ac.uk/blog/2017/04/prescribing-data-bnf-codes/
[1]: https://applications.nhsbsa.nhs.uk/infosystems/data/showDataSelector.do?reportId=126
