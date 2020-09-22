from collections import defaultdict

from coding_systems.ctv3 import coding_system as ctv3
from coding_systems.ctv3.models import Concept as CTV3Concept
from coding_systems.snomedct import coding_system as snomedct
from coding_systems.snomedct.models import Concept as SCTConcept
from coding_systems.snomedct.models import QueryTableRecord

from .models import Mapping


def ctv3_to_snomedct(ctv3_ids):
    # Find all active SNOMED CT concepts with assured mappings from CTV3
    # concepts.
    snomedct_ids = set(
        SCTConcept.objects.filter(
            active=True,
            ctv3_mappings__ctv3_concept_id__in=ctv3_ids,
            ctv3_mappings__map_status=True,
            ctv3_mappings__is_assured=True,
        ).values_list("id", flat=True)
    )

    # Find all active SNOMED CT concepts with assured mappings from leaf CTV3
    # concepts.
    leaf_ctv3_ids = CTV3Concept.objects.filter(
        read_code__in=ctv3_ids, children=None
    ).values_list("read_code", flat=True)

    ctv3_leaf_snomedct_ids = set(
        SCTConcept.objects.filter(
            active=True,
            ctv3_mappings__ctv3_concept_id__in=leaf_ctv3_ids,
            ctv3_mappings__map_status=True,
            ctv3_mappings__is_assured=True,
        ).values_list("id", flat=True)
    )

    # Find all SNOMED CT concepts that are descendants of those with assured
    # mappings from leaf CTV3 concepts.
    descendant_ids = {
        child_id
        for (parent_id, child_id) in snomedct.descendant_relationships(
            list(ctv3_leaf_snomedct_ids)
        )
    } - snomedct_ids

    active_ids = snomedct_ids | descendant_ids

    # Find all inactive SNOMED CT concepts that map to these active concepts
    # via the Query Table.
    query_table_subtype_ids = set(
        QueryTableRecord.objects.filter(supertype_id__in=active_ids)
        .values_list("subtype_id", flat=True)
        .distinct()
    )
    inactive_ids = query_table_subtype_ids - active_ids

    # Build mapping from SNOMED CT ID to CTV3 ID.
    all_ids = snomedct_ids | ctv3_leaf_snomedct_ids | descendant_ids | inactive_ids

    snomedct_id_to_ctv3_id = defaultdict(list)
    for mapping in Mapping.objects.filter(
        sct_concept_id__in=all_ids, map_status=True, is_assured=True
    ):
        snomedct_id_to_ctv3_id[mapping.sct_concept_id].append(mapping.ctv3_concept_id)

    snomedct_id_to_name = snomedct.lookup_names(all_ids)
    snomedct_id_to_active = {
        concept.id: concept.active
        for concept in SCTConcept.objects.filter(id__in=all_ids)
    }

    records = []
    for ids, notes in [
        (snomedct_ids, "direct mapping"),
        (descendant_ids, "descendant of concept mapped from leaf"),
        (inactive_ids, "via Query Table"),
    ]:
        for snomedct_id in ids:
            records.append(
                {
                    "id": snomedct_id,
                    "name": snomedct_id_to_name[snomedct_id],
                    "active": snomedct_id_to_active[snomedct_id],
                    "ctv3_ids": snomedct_id_to_ctv3_id[snomedct_id],
                    "notes": notes,
                }
            )

    return records


def snomedct_to_ctv3(snomedct_ids):
    """Convert SNOMED CT Concept codes to CTV3 Concepts IDs."""
    ctv3_ids = set(
        CTV3Concept.objects.filter(
            snomedct_mappings__sct_concept_id__in=snomedct_ids,
            snomedct_mappings__map_status=True,
            snomedct_mappings__is_assured=True,
        ).values_list("pk", flat=True)
    )

    ctv3_id_to_snomedct_id = defaultdict(list)
    for mapping in Mapping.objects.filter(
        ctv3_concept_id__in=ctv3_ids, map_status=True, is_assured=True
    ).select_related("ctv3_concept"):
        ctv3_id_to_snomedct_id[mapping.ctv3_concept.read_code].append(
            mapping.sct_concept_id
        )

    code_to_name = ctv3.lookup_names(ctv3_ids)

    records = []
    for ctv3_id in ctv3_ids:
        records.append(
            {
                "id": ctv3_id,
                "name": code_to_name[ctv3_id],
                "snomedct_ids": ctv3_id_to_snomedct_id[ctv3_id],
                "notes": "direct mapping",
            }
        )

    return records
