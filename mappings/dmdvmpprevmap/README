# dm+d VMP previous mappings

dm+d VMP IDs sometimes change. In a single dm+d release, each VMP record may have a `vmp_prev` attribute, which indicates the ID by which this VMP was previously known. However, only the last ID is recorded, and VMP IDs can change more than once.

To map VMP IDs in a dm+d codelist to any previous or subsequent ID, we maintain a mapping of current to previous IDs across historical releases.

Historical data from March 2019 to 12 December 2022 has been extracted from the release downloads into a single CSV file on the volume block storage mounted on dokku3:

`/mnt/volume_opencodelists_coding_system_data/opencodelists/data/dmdvmpprevmap/dmd_vpid_vpidprev_mapping_20221208.csv.gz`

See `scripts/fetch_vmp_prev.py` for how to recreate or update this file.

For releases after 12 December 2022, the mappings are updated whenever a new release is imported.

If the historical data needs to be re-imported, it can be run with:

```sh
dokku run opencodelists python manage.py import_mapping_data dmdvmpprevmap \
  /coding_system_data_block_storage/data/dmdvmpprevmap/dmd_vpid_vpidprev_mapping_20221208.csv.gz
```
