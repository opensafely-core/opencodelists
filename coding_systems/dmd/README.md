# Dictionary of Medicines and Devices (dm+d)

dm+d codes are used to identify medicines and devices in use across the NHS.

For more details, see [our blog post](https://www.bennett.ox.ac.uk/blog/2019/08/what-is-the-dm-d-the-nhs-dictionary-of-medicines-and-devices/).

We obtain the raw data from [TRUD](https://isd.digital.nhs.uk/trud/users/authenticated/filters/0/categories/6/items/24/releases).

You will need an account to access TRUD, and may be asked for a reason when you sign up -- if so, mention OpenCodelists. On the TRUD release page, subscribe to the releases. For local testing, you will need your API key. Find it on your [account page](https://isd.digital.nhs.uk/trud/users/authenticated/filters/0/account/manage), and set the `TRUD_API_KEY` variable in your local `.env` file.

## Automated updates

dm+d updates are released weekly. The release number (11.3.0 in the example below) refers to the month and (zero-indexed) week of the current year.

The latest dm+d data is imported automatically, via a cron job that runs the script at `deploy/bin/import_latest_release.sh dmd` each Monday.

## Manual updates

To import the latest release, run:

```sh
./manage.py import_latest_data dmd DATA_DIR
```

- `DATA_DIR` is the path on the local filesystem to the directory where the release will be downloaded.

On the dokku3 host, the directory on the Block Storage volume is `/mnt/volume_opencodelists_coding_system_data/opencodelists/data/dmd/`. Dokku bind-mounts it into OpenCodelists application containers at `/coding_system_data_block_storage/data/dmd/`. Import the latest release with:

```sh
dokku run opencodelists python manage.py import_latest_data dmd \
  /coding_system_data_block_storage/data/dmd/ && dokku ps:restart opencodelists
```

If you need to import an earlier release, first identify the release number and valid-from date (both can be retrieved from the filename). To avoid confusion, label the release with the year as well as the release number.

The release will be retrieved via the TRUD API (as a zipfile, named something like `nhsbsa_dmd_11.3.0_20221128000001.zip`). Find the release number and valid-from date from the release page, and run:

```sh
dokku run opencodelists python manage.py import_coding_system_data dmd \
  DATA_DIR \
  --release RELEASE_NAME \
  --valid-from VALID_FROM \
  --import-ref IMPORT_REF
```

- `DATA_DIR` is the path inside the OpenCodelists application container to the download directory. For the application container on dokku3, use `/coding_system_data_block_storage/data/dmd/`.
- `RELEASE_NAME` is a short label for this coding system release: the release year/number as described above.
- `VALID_FROM` is the date that this release is valid from (not the date it is being imported into OpenCodelists), in `YYYY-MM-DD` format.
- `IMPORT_REF` is an optional long-form reference field for any other potential references or comments on this import if desired. Omit it to default to the name of the downloaded zipfile.
- If importing the latest release, optionally specify `--latest`. This will retrieve only the latest release from TRUD. It will fail if the release and valid-from dates provided are not for the latest release.

For the example above (release 11.3.0, valid from 2022-11-28), the data should be imported with:

```sh
dokku run opencodelists python manage.py import_coding_system_data dmd \
  /coding_system_data_block_storage/data/dmd/ \
  --release '2022 11.3.0' \
  --valid-from 2022-11-28
```

After importing, restart the OpenCodelists app:

```sh
dokku ps:restart opencodelists
```
