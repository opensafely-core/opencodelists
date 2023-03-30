import uuid
from datetime import datetime

from django.urls import reverse

from codelists.tests.helpers import csv_builder
from coding_systems.ctv3.models import RawConcept, RawTerm, TPPConcept
from coding_systems.snomedct.models import Concept as SCTConcept
from mappings.ctv3sctmap2.models import Mapping


def setup_mapping():
    # construct a mapping between a SNOMED CT from the fixture data and CTV3 codes
    # Code 439656005 (Arthritis of elbow) maps to 2 CTV3 codes
    snomedct_db = "snomedct_test_20200101"
    ctv3_db = "ctv3_test_20200101"
    snomedct_concept = SCTConcept.objects.using(snomedct_db).get(id="439656005")
    ctv3_term = RawTerm.objects.using(ctv3_db).create(term_id="Y700y")
    for code, term_type, description in [
        ("N06z2", "S", "(Arthropathy NOS, of the upper arm) or (elbow arthritis NOS)"),
        ("X7009", "P", "Elbow arthritis NOS"),
    ]:
        ctv3_concept = RawConcept.objects.using(ctv3_db).create(
            read_code=code, another_concept_id=code, status=term_type
        )
        ctv3_concept.terms.add(ctv3_term)
        TPPConcept.objects.using(ctv3_db).create(
            read_code=code, description=description
        )
        Mapping.objects.create(
            id=uuid.uuid4(),
            sct_concept=snomedct_concept,
            sct_description=snomedct_concept.descriptions.first(),
            ctv3_concept=ctv3_concept,
            ctv3_term=ctv3_term,
            is_assured=True,
            map_status=True,
            effective_date=datetime(2020, 1, 1),
        )


def test_convert_full_mapping(client, disorder_of_elbow_csv_data):
    setup_mapping()
    data = {
        "from_coding_system_id": "snomedct",
        "to_coding_system_id": "ctv3",
        "csv_data": csv_builder(disorder_of_elbow_csv_data),
        "type": "full",
    }
    response = client.post(reverse("conversions:convert"), data)
    content = response.content.decode()
    # The two CTV3 codes that have mappings to a SNOMED CT are included
    assert content == (
        "snomedct_id,snomedct_name,ctv3_id,ctv3_name\r\n"
        '439656005,Arthritis of elbow (disorder),N06z2,"(Arthropathy NOS, of the upper arm) or (elbow arthritis NOS)"\r\n'
        "439656005,Arthritis of elbow (disorder),X7009,Elbow arthritis NOS\r\n"
    )


def test_convert_to_codes_only(client, disorder_of_elbow_csv_data):
    setup_mapping()
    data = {
        "from_coding_system_id": "snomedct",
        "to_coding_system_id": "ctv3",
        "csv_data": csv_builder(disorder_of_elbow_csv_data),
        "type": "to-codes-only",
    }
    response = client.post(reverse("conversions:convert"), data)
    # The two CTV3 codes that have mappings to a SNOMED CT are included
    content = response.content.decode()
    assert content == (
        "ctv3_id,ctv3_name\r\n"
        'N06z2,"(Arthropathy NOS, of the upper arm) or (elbow arthritis NOS)"\r\n'
        "X7009,Elbow arthritis NOS\r\n"
    )
