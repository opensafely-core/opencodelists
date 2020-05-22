import csv

from django.core.management import BaseCommand

from codelists.models import Codelist
from mappings.ctv3sctmap2.mappers import read_code_to_snomedct_concepts


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("out_path")

    def handle(self, out_path, **kwargs):
        f = open(out_path, "w")
        writer = csv.DictWriter(f, ["codelist", "read_code"])
        writer.writeheader()

        for cl in Codelist.objects.filter(coding_system_id__in=["ctv3", "ctv3tpp"]):
            print(cl.slug)
            code_to_snomed_concepts = read_code_to_snomedct_concepts(cl.codes)
            unmapped_ctv3_codes = [
                code
                for code, concepts in code_to_snomed_concepts.items()
                if not concepts
            ]

            for code in sorted(unmapped_ctv3_codes):
                writer.writerow({"codelist": cl.slug, "read_code": code})

        f.close()
