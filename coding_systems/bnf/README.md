BNF
---

BNF codes are used to identify anything that is prescribed in England (and maybe elsewhere).

For more details, see [our most popular blog post][0].

We obtain the data from the BSA.
New releases are published annually, sometimes with unannounced mid-year updates.
[The release page][1] displays the date and number of each release.
For example, in "01-01-2024 : 86", "01-01-2024" is the date and "86" is the number.
The release page displays mid-year updates using the same dates and numbers as their associated releases.
The date of a mid-year update is contained in the name of the associated zipfile.
For example, in `20240502_1714657404842_BNF_Code_Information.zip`, the date of the mid-year update is "20240502".
The number of a mid-year update is the same as that of the associated release.

Download and copy the latest release's zipfile to the BNF data folder on dokku3,
at `/var/lib/dokku/data/storage/opencodelists/data/bnf/`.

To import the data, run:

```sh
./manage.py import_coding_system_data bnf
/storage/data/bnf/<zipfile>
--release <release_name>
--valid-from <valid_from>
--import-ref <import_ref>
```

- `release_name` is the name of the release in `<number> (<date>)` format.
  `<number>` is the number of the release.
  (Remember that the number of a mid-year update is the same as that of the associated release.)
  `<date>` is the date of the release/mid-year update in `YYYY-MM-DD` format.
- `valid_from` is the date of the release/mid-year update in `YYYY-MM-DD` format.
  (It is *not* the date the data are imported into OpenCodelists.)
- `import_ref` is an optional reference for any other information. Include the name of the zipfile.

For the example above (`20240502_1714657404842_BNF_Code_Information.zip`),
the data should be imported with:

```sh
dokku run opencodelists python manage.py import_coding_system_data bnf
/storage/data/bnf/20240502_1714657404842_BNF_Code_Information.zip
--release '86 (2024-05-02)'
--valid-from 2024-05-02
--import-ref 20240502_1714657404842_BNF_Code_Information.zip
```

After importing, restart the opencodelists app with:

```sh
dokku ps:restart opencodelists
```

[0]: https://www.bennett.ox.ac.uk/blog/2017/04/prescribing-data-bnf-codes/
[1]: https://applications.nhsbsa.nhs.uk/infosystems/data/showDataSelector.do?reportId=126
