from coding_systems.snomedct.models import Concept as SnomedCTConcept

from .models import Mapping


def read_codes_to_snomedct_concepts(read_codes):
    mappings = Mapping.objects.filter(ctv3_concept__in=read_codes)
    mapped_read_codes = {m.ctv3_concept_id for m in mappings}
    unmapped_read_codes = [rc for rc in read_codes if rc not in mapped_read_codes]

    snomedct_concepts = SnomedCTConcept.objects.filter(
        ctv3_mappings__in=mappings
    ).distinct()

    return snomedct_concepts, unmapped_read_codes
