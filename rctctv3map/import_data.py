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
                "rctctv3map*.txt",
            )
        )
        assert len(paths) == 1

        with open(paths[0]) as f:
            reader = csv.reader(f, delimiter="\t")
            next(reader)
            for r in reader:
                r[9] = r[9] == "1"  # MAPSTATUS
                r[10] = parse_date(r[10])  # EFFECTIVEDATE

                if not r[9]:
                    continue
                yield r

    with transaction.atomic():
        Mapping.objects.all().delete()
        Mapping.objects.bulk_create(Mapping(*r) for r in load_records())


def parse_date(datestr):
    return datetime.date(int(datestr[:4]), int(datestr[4:6]), int(datestr[6:]))
