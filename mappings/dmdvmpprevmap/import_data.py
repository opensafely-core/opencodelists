import csv
import gzip

from django.db import transaction
from tqdm import tqdm

from .models import Mapping


def import_data(filename):
    def load_records():
        with gzip.open(filename, "rt") as infile:
            reader = csv.DictReader(infile)
            for row in reader:
                yield row["vpid"], row["vpidprev"]

    with transaction.atomic():
        for vpid, vpidprev in tqdm(load_records(), desc="Loading records"):
            Mapping.objects.get_or_create(id=vpid, vpidprev=vpidprev)
