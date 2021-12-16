import csv
import os

from django.db import transaction

from coding_systems.ctv3.models import TPPConcept, TPPRelationship


def run(release_dir):
    def load_records(filename, delimiter):
        with open(
            os.path.join(release_dir, filename + ".csv"), encoding="latin-1"
        ) as f:
            yield from csv.DictReader(f, delimiter=delimiter)

    with transaction.atomic():
        TPPRelationship.objects.all().delete()
        TPPConcept.objects.all().delete()

        TPPConcept.objects.bulk_create(
            TPPConcept(read_code=r["CTV3Code"], description=r["Description"])
            for r in load_records("ctv3dictionary", "|")
        )

        TPPRelationship.objects.bulk_create(
            TPPRelationship(
                ancestor_id=r["ParentCTV3Code"],
                descendant_id=r["ChildCTV3Code"],
                distance=r["ChildToParentDistance"],
            )
            for r in load_records("ctv3hierarchy", ",")
        )
