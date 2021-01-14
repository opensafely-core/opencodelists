"""Import ICD-10 data from
https://apps.who.int/classifications/apps/icd/ClassificationDownload/DLArea/Download.aspx"""

from django.db import transaction
from lxml import etree

from .models import Concept


def import_data(release_path):
    with open(release_path) as f:
        doc = etree.parse(f)

    with transaction.atomic():
        Concept.objects.all().delete()
        Concept.objects.bulk_create(Concept(**record) for record in load_concepts(doc))


def load_concepts(doc):
    root = doc.getroot()

    for e in root.findall("Class"):
        label = e.find("Rubric[@kind='preferredLong']/Label")
        if label is None:
            label = e.find("Rubric[@kind='preferred']/Label")
        term = " ".join(label.itertext())

        superclass = e.find("SuperClass")
        if superclass is not None:
            parent_id = superclass.get("code")
        else:
            parent_id = None

        yield {
            "code": e.get("code"),
            "kind": e.get("kind"),
            "term": term,
            "parent_id": parent_id,
        }


if __name__ == "__main__":
    import sys

    import_data(sys.argv[1])
