# BNF to dm+d (SNOMED) mappings

dm+d codes are used to identify medicines and devices in use across the NHS.

Codelists are typically built using pseudoBNF and converted to dm+d for use in study definitions.

For more details, see our blog posts about [dm+d](https://www.bennett.ox.ac.uk/blog/2019/08/what-is-the-dm-d-the-nhs-dictionary-of-medicines-and-devices/) and [the differences between BNF, dm+d, and SNOMED CT codes](https://www.bennett.ox.ac.uk/blog/2022/11/difference-between-bnf-dm-d-and-snomed-ct-codes/).

We obtain the mapping data from the [NHS Business Services Authority](https://www.nhsbsa.nhs.uk/prescription-data/understanding-our-data/bnf-snomed-mapping). New mapping data is released monthly.

## Automated updates

The latest mapping file is imported automatically, via a cron job that runs the script at `deploy/bin/import_latest_release.sh mappings.bnfdmd` each Wednesday. The directory on the Block Storage volume is available at `/mnt/volume_opencodelists_coding_system_data/opencodelists/data/mappings.bnfdmd/` on the dokku3 host and is bind-mounted into OpenCodelists application containers at `/coding_system_data_block_storage/data/mappings.bnfdmd/`.

If the latest release file already exists, it will not be reimported. After a failed import, you may need to delete the corresponding release file from the directory on the dokku3 host to allow the import to run again.

## Manual updates

On the download page, download the latest release. This will be a zip file named something like `SNOMED - BNF mapping document September 2022.zip`, containing a single XLSX file.

To import the data, unzip the file and run:

```sh
./manage.py import_mapping_data bnfdmd XLSX_FILE
```

- `XLSX_FILE` is the path to the XLSX file extracted from the release zip file.

As a simple post-import check, compare the reported number of imported rows with the number of spreadsheet rows that contain both a BNF code and a dm+d code.
