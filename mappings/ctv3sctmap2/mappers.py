from collections import defaultdict

from coding_systems.ctv3.models import Concept as CTV3Concept
from coding_systems.snomedct.coding_system import descendant_relationships, lookup_names
from coding_systems.snomedct.models import Concept as SCTConcept
from coding_systems.snomedct.models import HistorySubstitution, QueryTableRecord

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
        for (parent_id, child_id) in descendant_relationships(
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

    # Find all extra SNOMED CT concepts that are mapped to from these inactive
    # concepts via the History Substitution Table.
    history_substitution_new_ids = set(
        HistorySubstitution.objects.filter(old_concept_id__in=inactive_ids)
        .values_list("new_concept_id", flat=True)
        .distinct()
    )
    extra_ids = history_substitution_new_ids - active_ids

    # Build mapping from SNOMED CT ID to CTV3 ID.
    all_ids = (
        snomedct_ids
        | ctv3_leaf_snomedct_ids
        | descendant_ids
        | inactive_ids
        | extra_ids
    )

    snomedct_id_to_ctv3_id = defaultdict(list)
    for mapping in Mapping.objects.filter(
        sct_concept_id__in=all_ids, map_status=True, is_assured=True
    ):
        snomedct_id_to_ctv3_id[mapping.sct_concept_id].append(mapping.ctv3_concept_id)

    snomedct_id_to_name = lookup_names(all_ids)
    snomedct_id_to_active = {
        concept.id: concept.active
        for concept in SCTConcept.objects.filter(id__in=all_ids)
    }

    records = []
    for ids, notes in [
        (snomedct_ids, "direct mapping"),
        (descendant_ids, "descendant of concept mapped from leaf"),
        (inactive_ids, "via Query Table"),
        (extra_ids, "via History Substitution Table"),
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
