import datetime
import uuid

from coding_systems.ctv3.models import RawConcept as CTV3Concept
from coding_systems.ctv3.models import RawTerm
from coding_systems.snomedct.models import Concept as SCTConcept
from coding_systems.snomedct.models import Description
from mappings.ctv3sctmap2.mappers import get_mappings
from mappings.ctv3sctmap2.models import Mapping


def test_get_mappings():
    """Test snomedct_to_ctv3 returns the correct format."""
    effective_time = datetime.datetime(2020, 1, 1)

    # construct a mapping between a pair of SNOMED CT and CTV3 codes
    snomed_concept = SCTConcept(
        id="54219001", effective_time=effective_time, active=True
    )
    snomed_concept.definition_status = snomed_concept
    snomed_concept.module = snomed_concept
    snomed_concept.save()

    description = Description.objects.create(
        active=True,
        case_significance=snomed_concept,
        concept=snomed_concept,
        effective_time=effective_time,
        module=snomed_concept,
        type=snomed_concept,
    )

    ctv3_concept = CTV3Concept(
        read_code="J650.",
    )
    ctv3_concept.another_concept = ctv3_concept
    ctv3_concept.save()

    term = RawTerm.objects.create()
    ctv3_concept.terms.add(term)

    Mapping.objects.create(
        id=uuid.uuid4(),
        sct_concept=snomed_concept,
        sct_description=description,
        ctv3_concept=ctv3_concept,
        ctv3_term=term,
        is_assured=True,
        map_status=True,
        effective_date=effective_time,
    )

    expected = [{"ctv3": "J650.", "snomedct": "54219001"}]
    assert get_mappings(ctv3_ids=["J650."]) == expected
    assert get_mappings(snomedct_ids=["54219001"]) == expected
    assert get_mappings(ctv3_ids=["J650."], snomedct_ids=["54219001"]) == expected
