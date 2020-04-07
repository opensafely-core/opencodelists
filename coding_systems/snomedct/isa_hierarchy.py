import os
from functools import lru_cache

import networkx as nx
from django.conf import settings

from .models import (
    FULLY_SPECIFIED_NAME,
    IS_A,
    STATED_RELATIONSHIP,
    Description,
    Relationship,
)

PICKLE_PATH = os.path.join(
    settings.BASE_DIR, "coding_systems", "snomedct", "data", "isa_hierarchy.pickle"
)


def build_hierarchy():
    relationships = Relationship.objects.filter(
        active=True, type_id=IS_A, characteristic_type_id=STATED_RELATIONSHIP
    )
    concept_ids = set(r.source_id for r in relationships) | set(
        r.destination_id for r in relationships
    )
    descriptions = Description.objects.filter(
        active=True, type_id=FULLY_SPECIFIED_NAME, concept_id__in=concept_ids
    ).select_related("concept")

    graph = nx.DiGraph()

    for d in descriptions:
        concept = d.concept
        concept.fully_specified_name = d.term
        graph.add_node(concept.id, concept=concept)

    for r in relationships:
        graph.add_edge(r.destination_id, r.source_id)

    return graph


def dump_hierarchy():
    hierarchy = build_hierarchy()
    nx.readwrite.write_gpickle(hierarchy, PICKLE_PATH)


@lru_cache()
def load_hierarchy():
    print("loading hierarchy...")
    hierarchy = nx.readwrite.read_gpickle(PICKLE_PATH)
    print("...loaded hierarchy")
    return hierarchy
