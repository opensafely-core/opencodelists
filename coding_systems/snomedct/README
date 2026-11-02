# SNOMED CT

[SNOMED CT](https://www.snomed.org/) aims to be the "global common language for clinical terms".

There is an international release and various national releases.

We obtain the raw data from [TRUD](https://isd.digital.nhs.uk/trud/users/authenticated/filters/0/categories/26/items/101/releases), and from this we import:

- the International release
- the UK edition
- the UK Clinical Extension

You will need an account to access TRUD, and may be asked for a reason when you sign up -- if so, mention OpenCodelists.

For local testing, you will need your API key. Find it on your [account page](https://isd.digital.nhs.uk/trud/users/authenticated/filters/0/account/manage), and set the `TRUD_API_KEY` variable in your local `.env` file.

## Automated updates

Updates are released every few months.

The latest SNOMED CT data is imported automatically, via a cron job that runs the script at `deploy/bin/import_latest_release.sh snomedct` each Tuesday. If the latest release already exists, it will not be reimported.

## Manual updates

To import the latest release, run:

```sh
./manage.py import_latest_data snomedct DATA_DIR
```

- `DATA_DIR` is the path to the directory where the release will be downloaded.

On dokku3, import the latest release with:

```sh
dokku run opencodelists python manage.py import_latest_data snomedct \
  /coding_system_data_block_storage/data/snomedct/ && dokku ps:restart opencodelists
```

If you need to download an earlier release, go to the TRUD release page and identify the required release, which will be a zip file named something like `uk_sct2cl_32.10.0_20220216000001Z.zip`. You do not need to download the file, as it will be retrieved via the API. The release number can be obtained from the filename. The TRUD release page states the release date, which should be used as the valid-from date. This is usually a few days after the date in the zip filename (release 32.10.0 has a release date of 23 February 2022).

To import the data, run:

```sh
dokku run opencodelists python manage.py import_coding_system_data snomedct \
  DATA_DIR \
  --release RELEASE_NAME \
  --valid-from VALID_FROM \
  --import-ref IMPORT_REF
```

- `DATA_DIR` is the download directory on dokku3: `/coding_system_data_block_storage/data/snomedct/`.
- `RELEASE_NAME` is the official version number described above.
- `VALID_FROM` is the release date in `YYYY-MM-DD` format, not the date the data are imported into OpenCodelists.
- `IMPORT_REF` is an optional reference for additional information. Omit it to default to the downloaded zip filename.
- If importing the latest release, optionally specify `--latest`. This will retrieve only the latest release from TRUD. It will fail if the release and valid-from dates provided are not for the latest release.

For the example file `uk_sct2cl_32.10.0_20220216000001Z.zip`, use:

```sh
dokku run opencodelists python manage.py import_coding_system_data snomedct \
  /coding_system_data_block_storage/data/snomedct/ \
  --release 32.10.0 \
  --valid-from 2022-02-23
```

After importing, restart the OpenCodelists app:

```sh
dokku ps:restart opencodelists
```
