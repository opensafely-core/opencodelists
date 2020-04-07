import csv
import datetime
import glob
import os

from django.db import transaction

from .models import Mapping


def import_data(release_dir):
    def load_records():
        paths = glob.glob(
            os.path.join(
                release_dir,
                "Mapping Tables",
                "Updated",
                "Clinically Assured",
                "ctv3sctmap2*.txt",
            )
        )
        assert len(paths) == 1

        with open(paths[0]) as f:
            reader = csv.reader(f, delimiter="\t")
            next(reader)
            for r in reader:
                if r[4] == "_DRUG":  # SCT_CONCEPTID
                    r[4] = None
                    r[5] = None
                r[6] = r[6] == "1"  # MAPSTATUS
                r[7] = parse_date(r[7])  # EFFECTIVEDATE
                r[8] = r[8] == "1"  # IS_ASSURED

                if not r[6]:
                    continue
                yield r

    with transaction.atomic():
        Mapping.objects.all().delete()
        Mapping.objects.bulk_create(Mapping(*r) for r in load_records())


def parse_date(datestr):
    return datetime.date(int(datestr[:4]), int(datestr[4:6]), int(datestr[6:]))
