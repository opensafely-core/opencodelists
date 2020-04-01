import os

from dbfread import DBF

from .models import Concept, ConceptHierarchy, ConceptTermMapping, Term


def import_data(release_dir):
    def load_records(filename):
        path = os.path.join(release_dir, "Standard", "V2", filename)
        yield from DBF(path, encoding="latin1", lowernames=True)

    Concept.objects.bulk_create(
        Concept(read_code=r["readcode"]) for r in load_records("CONCEPT.DBF")
    )

    ConceptHierarchy.objects.bulk_create(
        ConceptHierarchy(child_id=r["cc"], parent_id=r["pcc"])
        for r in load_records("HIER.DBF")
    )

    term_id_to_long_term_name = {
        r["termid"]: r["term198"] for r in load_records("TERM198.DBF")
    }
    term_records = [
        dict(**r, **{"term198": term_id_to_long_term_name.get("termid", "")})
        for r in (load_records("TERM.DBF"))
    ]

    Term.objects.bulk_create(
        Term(
            term_id=r["termid"],
            name_1=r["term30"],
            name_2=r["term60"],
            name_3=r["term198"],
        )
        for r in term_records
    )

    ConceptTermMapping.objects.bulk_create(
        ConceptTermMapping(concept_id=r["cc"], term_id=r["termid"])
        for r in load_records("DESC.DBF")
    )
