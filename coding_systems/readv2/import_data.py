import csv
import os

from .models import Concept


def import_data(release_dir):
    path = os.path.join(release_dir, "V2", "Unified", "Corev2.all")
    with open(path) as f:
        Concept.objects.bulk_create(Concept(*row) for row in csv.reader(f))
