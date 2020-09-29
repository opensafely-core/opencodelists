import collections

from opencodelists.db_utils import query

from .models import TPPConcept, TPPRelationship

name = "CTV3 (Read V3)"
short_name = "CTV3"

root = "....."


def lookup_names(codes):
    return dict(
        TPPConcept.objects.filter(read_code__in=codes).values_list(
            "read_code", "description"
        )
    )


def search(term):
    # TODO: search synomyms as well.
    return set(
        TPPConcept.objects.filter(description__contains=term).values_list(
            "read_code", flat=True
        )
    )


def ancestor_relationships(codes):
    codes = list(codes)
    relationship_table = TPPRelationship._meta.db_table
    placeholders = ", ".join(["%s"] * len(codes))
    sql = f"""
    WITH RECURSIVE tree(ancestor_id, descendant_id) AS (
      SELECT ancestor_id, descendant_id
      FROM {relationship_table}
      WHERE descendant_id IN ({placeholders}) AND distance = 1

      UNION

      SELECT r.ancestor_id, r.descendant_id
      FROM {relationship_table} r
      INNER JOIN tree t
        ON r.descendant_id = t.ancestor_id
      WHERE distance = 1
    )

    SELECT ancestor_id, descendant_id FROM tree
    """

    return query(sql, codes)


def descendant_relationships(codes):
    codes = list(codes)
    relationship_table = TPPRelationship._meta.db_table
    placeholders = ", ".join(["%s"] * len(codes))
    sql = f"""
    WITH RECURSIVE tree(ancestor_id, descendant_id) AS (
      SELECT ancestor_id, descendant_id
      FROM {relationship_table}
      WHERE ancestor_id IN ({placeholders}) AND distance = 1

      UNION

      SELECT r.ancestor_id, r.descendant_id
      FROM {relationship_table} r
      INNER JOIN tree t
        ON r.ancestor_id = t.descendant_id
      WHERE distance = 1
    )

    SELECT ancestor_id, descendant_id FROM tree
    """

    return query(sql, codes)


def code_to_term(codes, hierarchy):
    return lookup_names(codes)


def codes_by_type(codes, hierarchy):
    """
    Group codes by their Concept "types"

    We treat the children of CTV3's root Concept as types.  However, CTV3
    Concepts can be descended from more than one of these "types", so each
    grouping of codes can have an overlap with other groupings.
    """

    if not codes:
        # The hierarchy will be empty, and so looking up the children of the
        # root will fail.
        return {}

    # Treat children of CTV3 root as types
    types = hierarchy.child_map[root]
    concepts = TPPConcept.objects.filter(read_code__in=types)
    terms_by_type = {c.read_code: c.description for c in concepts}

    lookup = collections.defaultdict(list)
    for code in codes:
        # get groups for this
        groups = hierarchy.ancestors(code) & types

        # Remove Concept "Additional values" when there is at least one other
        # type to use.
        if len(groups) > 1 and "X78tJ" in groups:
            groups.remove("X78tJ")

        for group_code in groups:
            group_term = terms_by_type[group_code]
            lookup[group_term].append(code)

    return dict(lookup)
