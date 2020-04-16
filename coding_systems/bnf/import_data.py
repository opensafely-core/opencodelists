import csv
import glob
import os

from django.db import transaction

from .models import (
    Chapter,
    ChemicalSubstance,
    Paragraph,
    Presentation,
    Product,
    Section,
    Subparagraph,
)


def import_data(release_dir):
    paths = glob.glob(os.path.join(release_dir, "*.csv"))
    assert len(paths) == 1
    path = paths[0]

    chapters = set()
    sections = set()
    paragraphs = set()
    subparagraphs = set()
    chemical_substances = set()
    products = set()
    presentations = set()

    with open(path) as f:
        for r in csv.DictReader(f):
            chapters.add((r["BNF Chapter Code"], r["BNF Chapter"]))
            sections.add((r["BNF Section Code"], r["BNF Section"]))
            paragraphs.add((r["BNF Paragraph Code"], r["BNF Paragraph"]))
            subparagraphs.add((r["BNF Subparagraph Code"], r["BNF Subparagraph"]))
            chemical_substances.add(
                (r["BNF Chemical Substance Code"], r["BNF Chemical Substance"])
            )
            products.add((r["BNF Product Code"], r["BNF Product"]))
            presentations.add((r["BNF Presentation Code"], r["BNF Presentation"]))

    with transaction.atomic():
        Chapter.objects.all().delete()
        Chapter.objects.bulk_create(
            Chapter(code, name) for code, name in sorted(chapters)
        )

        Section.objects.all().delete()
        Section.objects.bulk_create(
            Section(code, name) for code, name in sorted(sections)
        )

        Paragraph.objects.all().delete()
        Paragraph.objects.bulk_create(
            Paragraph(code, name)
            for code, name in sorted(paragraphs)
            if "DUMMY" not in name
        )

        Subparagraph.objects.all().delete()
        Subparagraph.objects.bulk_create(
            Subparagraph(code, name)
            for code, name in sorted(subparagraphs)
            if "DUMMY" not in name
        )

        ChemicalSubstance.objects.all().delete()
        ChemicalSubstance.objects.bulk_create(
            ChemicalSubstance(code, name)
            for code, name in sorted(chemical_substances)
            if "DUMMY" not in name
        )

        Product.objects.all().delete()
        Product.objects.bulk_create(
            Product(code, name)
            for code, name in sorted(products)
            if "DUMMY" not in name
        )

        Presentation.objects.all().delete()
        Presentation.objects.bulk_create(
            Presentation(code, name)
            for code, name in sorted(presentations)
            if "DUMMY" not in name
        )
