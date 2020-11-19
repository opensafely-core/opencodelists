import csv

from django.db import transaction
from django.db.utils import IntegrityError

from .coding_system import CODING_SYSTEMS
from .models import Codelist, CodelistVersion, Publisher


class ImportCodelistError(Exception):
    pass


def import_codelist(publisher_slug, codelist_slug, coding_system_id, tag, csv_path):
    if coding_system_id not in CODING_SYSTEMS:
        raise ImportCodelistError("Invalid coding_system")

    with transaction.atomic():
        publisher, _ = Publisher.objects.get_or_create(slug=publisher_slug)

        try:
            cl, _ = Codelist.objects.get_or_create(
                publisher=publisher,
                slug=codelist_slug,
                coding_system_id=coding_system_id,
            )
        except IntegrityError:
            cl = Codelist.objects.get(publisher=publisher, slug=codelist_slug)
            raise ImportCodelistError(
                "Codelist {}/{} already exists with coding system {}".format(
                    publisher_slug, codelist_slug, cl.coding_system_id
                )
            )

        try:
            clv = CodelistVersion.objects.create(codelist=cl, tag=tag)
        except IntegrityError:
            raise ImportCodelistError(
                "Version {} already exists for codelist {}/{}".format(
                    tag, publisher_slug, codelist_slug
                )
            )

        try:
            with open(csv_path) as f:
                codes = [r[0] for r in csv.reader(f)]
        except FileNotFoundError:
            raise ImportCodelistError(
                "Could not open '{}' for reading".format(csv_path)
            )

        clv.definition = "\n".join(codes)
        clv.save()
