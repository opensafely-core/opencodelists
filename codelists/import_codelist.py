import csv

from django.db import transaction
from django.db.utils import IntegrityError

from .models import CODING_SYSTEMS, Codelist, CodelistMember, CodelistVersion, Publisher


class ImportCodelistError(Exception):
    pass


def import_codelist(
    publisher_slug, codelist_slug, coding_system, version_str, csv_path
):
    coding_systems = [tpl[0] for tpl in CODING_SYSTEMS]
    if coding_system not in coding_systems:
        raise ImportCodelistError("Invalid coding_system")

    with transaction.atomic():
        publisher, _ = Publisher.objects.get_or_create(slug=publisher_slug)

        try:
            cl, _ = Codelist.objects.get_or_create(
                publisher=publisher, slug=codelist_slug, coding_system=coding_system
            )
        except IntegrityError:
            cl = Codelist.objects.get(publisher=publisher, slug=codelist_slug)
            raise ImportCodelistError(
                "Codelist {}/{} already exists with coding system {}".format(
                    publisher_slug, codelist_slug, cl.coding_system
                )
            )

        try:
            clv = CodelistVersion.objects.create(codelist=cl, version_str=version_str)
        except IntegrityError:
            raise ImportCodelistError(
                "Version {} already exists for codelist {}/{}".format(
                    version_str, publisher_slug, codelist_slug
                )
            )

        try:
            with open(csv_path) as f:
                codes = [r[0] for r in csv.reader(f)]
        except FileNotFoundError:
            raise ImportCodelistError(
                "Could not open '{}' for reading".format(csv_path)
            )

        CodelistMember.objects.bulk_create(
            CodelistMember(codelist_version=clv, code=c) for c in codes
        )
