from opencodelists.db_utils import query

from .models import Concept, ConceptTermMapping

name = "CTV3 (Read V3)"
short_name = "CTV3"

root = "....."


def lookup_names(codes):
    qs = ConceptTermMapping.objects.filter(
        concept_id__in=codes, term_type=ConceptTermMapping.PREFERRED
    ).values("concept_id", "term__name_1", "term__name_2", "term__name_3")

    return {
        record["concept_id"]: (
            record["term__name_3"] or record["term__name_2"] or record["term__name_1"]
        )
        for record in qs
    }


def ancestor_relationships(codes):
    placeholders = ", ".join(["%s"] * len(codes))
    sql = f"""
    WITH RECURSIVE tree(parent_id, child_id) AS (
      SELECT parent_id, child_id
      FROM ctv3_concepthierarchy
      WHERE child_id IN ({placeholders})

      UNION

      SELECT h.parent_id, h.child_id
      FROM ctv3_concepthierarchy h
      INNER JOIN tree t
        ON h.child_id = t.parent_id
    )

    SELECT parent_id, child_id FROM tree
    """

    return query(sql, codes)


def descendant_relationships(codes):
    placeholders = ", ".join(["%s"] * len(codes))
    sql = f"""
    WITH RECURSIVE tree(parent_id, child_id) AS (
      SELECT parent_id, child_id
      FROM ctv3_concepthierarchy
      WHERE parent_id IN ({placeholders})

      UNION

      SELECT h.parent_id, h.child_id
      FROM ctv3_concepthierarchy h
      INNER JOIN tree t
        ON h.parent_id = t.child_id
    )

    SELECT parent_id, child_id FROM tree
    """

    return query(sql, codes)


def code_to_term(codes, hierarchy):
    concepts = Concept.objects.filter(read_code__in=hierarchy.nodes).prefetch_related(
        "terms"
    )
    return {c.read_code: c.preferred_term() for c in concepts}


def code_to_type(codes, hierarchy):
    """
    Create a mapping between a code and its Concept types

    We treat the children of CTV3's root Concept as types.  However, CTV3
    Concepts can be descended from more than one of these "types", so we use
    the first type.
    """
    types = hierarchy.child_map[root]
    concepts = Concept.objects.filter(read_code__in=types).prefetch_related("terms")
    terms_by_type = {c.read_code: c.preferred_term() for c in concepts}

    for code in codes:
        type_nodes = hierarchy.ancestors(code) & types

        # TODO: can we pass in codes bucketed by type to tree_tables?
        first = list(type_nodes)[0]
        term = terms_by_type[first]

        yield code, term
