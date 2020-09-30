import csv
import glob
import os

from django.db import transaction

from .models import TYPES, Concept


def import_data(release_dir):
    paths = glob.glob(os.path.join(release_dir, "*.csv"))
    assert len(paths) == 1
    path = paths[0]

    records = {type: set() for type in TYPES}

    with open(path) as f:
        for r in csv.DictReader(f):
            parent_code = None
            for type in TYPES:
                name = r[f"BNF {type}"]
                code = r[f"BNF {type} Code"]
                if "DUMMY" not in name:
                    records[type].add((code, name, parent_code))
                    parent_code = code

    with transaction.atomic():
        Concept.objects.all().delete()
        for type in TYPES:
            Concept.objects.bulk_create(
                Concept(code=code, name=name, type=type, parent_id=parent_code)
                for code, name, parent_code in sorted(records[type])
            )
