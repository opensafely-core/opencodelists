# CTV3

CTV3 is a retired system of clinical terms. It succeeded Read v2 and has been replaced by SNOMED CT. (The "CT" stands for "Clinical Terms" in both CTV3 and SNOMED CT.)

No new CTV3 codes are published, although TPP sometimes publishes new "Y codes" that look like CTV3 codes.

The last official CTV3 release was on 1 April 2018. This data is no longer available to download online, but can be retrieved from the zip file on the volume block storage mounted on dokku3. Place the zip file in the CTV3 data folder on the mounted volume block storage:

`/mnt/volume_opencodelists_coding_system_data/opencodelists/data/ctv3/nhs_readctv3_25.0.0_20180401000001.zip`

TPP extracts CTV3 codes from the database by running all the jobs in [this workspace](https://jobs.opensafely.org/datalab/opensafely-testing/tpp-ctv3-codes/) and following the [usual process for checking and releasing output files](https://docs.opensafely.org/releasing-files/). The two output files needed to import the data into OpenCodelists are:

- `ctv3_dictionary.csv.gz`
- `ctv3_hierarchy.csv.gz`

Copy these files into a subfolder named with the extraction date in the CTV3 data folder on the dokku3 mounted volume. For example, if the files were extracted on 28 November 2023, copy them to:

`/mnt/volume_opencodelists_coding_system_data/opencodelists/data/ctv3/2023-11-28/`

To import the data, run:

```sh
dokku run opencodelists python manage.py import_coding_system_data ctv3 \
  DATA_DIR \
  --release RELEASE_NAME \
  --valid-from VALID_FROM \
  --import-ref IMPORT_REF
```

- `DATA_DIR` is the path to the dated subfolder containing the extracted files on dokku3.
- `RELEASE_NAME` identifies the release. Include the last official CTV3 release date and the date the TPP extensions were extracted.
- `VALID_FROM` is the date the release is valid from in `YYYY-MM-DD` format, not the date it is imported into OpenCodelists.
- `IMPORT_REF` is an optional reference for additional information. Include the extraction date.

For the example directory above, use:

```sh
dokku run opencodelists python manage.py import_coding_system_data ctv3 \
  /coding_system_data_block_storage/data/ctv3/2023-11-28/ \
  --release '2018-04-01 with TPP extensions 2023-11-28' \
  --valid-from 2023-11-28 \
  --import-ref 'Extracted 2023-11-28'
```

After importing, restart the OpenCodelists app:

```sh
dokku ps:restart opencodelists
```
