import csv
import os

from .models import RawConcept, RawConceptHierarchy, RawConceptTermMapping, RawTerm


def import_data(release_dir):
    def load_records(filename):
        with open(os.path.join(release_dir, "V3", filename)) as f:
            yield from csv.reader(f, delimiter="|", quoting=csv.QUOTE_NONE)

    RawConcept.objects.bulk_create(
        RawConcept(
            read_code=r[0], status=r[1], unknown_field_2=r[2], another_concept_id=r[3]
        )
        for r in load_records("Concept.v3")
    )

    RawConceptHierarchy.objects.bulk_create(
        RawConceptHierarchy(child_id=r[0], parent_id=r[1], list_order=r[2])
        for r in load_records("V3hier.v3")
    )

    RawTerm.objects.bulk_create(
        RawTerm(term_id=r[0], status=r[1], name_1=r[2], name_2=r[3], name_3=r[4])
        for r in load_records("Terms.v3")
    )

    RawConceptTermMapping.objects.bulk_create(
        RawConceptTermMapping(concept_id=r[0], term_id=r[1], term_type=r[2])
        for r in load_records("Descrip.v3")
    )
