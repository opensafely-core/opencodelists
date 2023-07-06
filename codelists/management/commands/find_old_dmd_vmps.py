import csv

from django.core.management import BaseCommand

from codelists.models import CodelistVersion
from mappings.dmdvmpprevmap.mappers import vmp_ids_to_previous


class Command(BaseCommand):

    """
    Takes a dm+d codelist version, finds any VMP codes that have been superceded (by checking our
    vmp to vmp previous mapping), and uses the CSV file generated from historical OP data to
    report the date the change was first seen.

    Note: the OP CSV was last generated in Dec 2022; any changes after this date won't be in it
    unless we re-extract all the data from OP. Better would be to update the Mapping model in
    dmdvmpprevmap/models.py to have knowledge of the date it first changed. We can do
    for changes up to Dec 2022 using the OP CSV, any others after that will need to check the
    dm+d releases to confirm when it was first seen. Going forward, the dm+d import_data command
    should add a date of change to the Mapping model for any new mappings found.
    """

    def add_arguments(self, parser):
        parser.add_argument("version_hash")
        parser.add_argument(
            "mapping_csv",
            help="Path to mapping csv, named something like dmd_vpid_vpidprev_mapping_2022-12-08.csv",
        )

    def handle(self, version_hash, mapping_csv, **kwargs):
        version = next(
            (
                version
                for version in CodelistVersion.objects.all()
                if version.hash == version_hash
            ),
            None,
        )
        if version is None:
            self.stderr.write(f"No CodelistVersion found with hash '{version_hash}'")
            return
        elif version.coding_system_id != "dmd":
            self.stderr.write(
                f"CodelistVersion '{version_hash}' is not a dm+d codelist)"
            )
            return

        codes = version.csv_data_for_download().split("\n")[1:-1]
        codes = [code.split(",")[0] for code in codes]
        mapping = vmp_ids_to_previous()
        superceded_codes = [it[1] for it in mapping]
        superceded_codes_in_codelist = set(superceded_codes) & set(codes)

        old_to_new = {
            old: new for new, old in mapping if old in superceded_codes_in_codelist
        }
        superceded_code_history = {}
        with open(mapping_csv) as in_f:
            reader = csv.DictReader(in_f)
            for row in reader:
                if (
                    row["vpidprev"] in old_to_new
                    and row["vpid"] == old_to_new[row["vpidprev"]]
                ):
                    row["date"] = row["source_file"].split("/")[6]
                    superceded_code_history.setdefault(row["vpidprev"], []).append(row)

        results = []
        for superceded_code, new_code in old_to_new.items():
            history = superceded_code_history[superceded_code]
            first_change = sorted(history, key=lambda x: x["date"])[0]
            results.append((superceded_code, new_code, first_change["date"]))

        self.stdout.write(
            "".join(
                heading.ljust(20)
                for heading in ["OLD CODE", "NEW CODE", "DATE CHANGE SEEN"]
            )
        )
        for result in results:
            self.stdout.write("".join(res.ljust(20) for res in result))
