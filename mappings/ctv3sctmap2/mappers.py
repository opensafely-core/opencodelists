from .models import Mapping


def get_mappings(ctv3_ids=None, snomedct_ids=None):
    """Return mappings between CTV3 and SNOMED CT concepts that are assured and
    have map_status=True (which means that the mapping is active).
    """

    assert ctv3_ids or snomedct_ids

    mappings = Mapping.objects.filter(is_assured=True, map_status=True)
    if ctv3_ids:
        mappings = mappings.filter(ctv3_concept_id__in=ctv3_ids)
    if snomedct_ids:
        mappings = mappings.filter(sct_concept_id__in=snomedct_ids)

    return [
        {"ctv3": m[0], "snomedct": m[1]}
        for m in mappings.values_list("ctv3_concept_id", "sct_concept_id")
    ]
