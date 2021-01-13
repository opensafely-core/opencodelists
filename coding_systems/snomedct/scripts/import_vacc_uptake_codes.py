import json

from codelists.actions import create_codelist_with_codes
from codelists.coding_systems import CODING_SYSTEMS
from codelists.definition2 import Definition2
from codelists.hierarchy import Hierarchy
from coding_systems.snomedct import ecl_parser
from opencodelists.models import Organisation


def run(path):
    """Create codelists based on PRIMIS vaccine uptake reporting documentation."""

    snomedct = CODING_SYSTEMS["snomedct"]

    primis, _ = Organisation.objects.get_or_create(
        slug="primis-covid19-vacc-uptake",
        defaults={
            "name": "PRIMIS Covid Vaccination Uptake Reporting",
            "url": "https://www.nottingham.ac.uk/primis/",
        },
    )

    with open(path) as f:
        records = json.load(f)

    for record in records:
        if (
            "See associated spreadsheet" in record["details"]
            or "dm+d" in record["details"]
        ):
            print(f"Skipping {record['name']} ({record['details']})")
            continue

        handled = ecl_parser.handle(record["details"])
        included = set(handled["included"])
        excluded = set(handled["excluded"])
        definition = Definition2(included, excluded)
        hierarchy = Hierarchy.from_codes(snomedct, included | excluded)
        codes = definition.codes(hierarchy)
        codelist = create_codelist_with_codes(
            owner=primis,
            slug=record["name"].lower(),
            name=record["title"],
            coding_system_id="snomedct",
            codes=codes,
        )
        codelist.description = f"Taken from the `{record['name']}` field in SARS-CoV2 COVID19 Vaccination Uptake Reporting Codes 20_21 v1, published by PRIMIS."
        codelist.save()
        clv = codelist.versions.get()
        clv.tag = "v1"
        clv.save()
        print(f"Imported {record['name']}, {len(codes)} codes")
