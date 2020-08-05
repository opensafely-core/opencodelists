from opencodelists.db_utils import query

from .models import FULLY_SPECIFIED_NAME, IS_A, Concept, Description

name = "SNOMED CT"
short_name = "SNOMED CT"

root = "138875005"


def lookup_names(codes):
    return {
        description.concept_id: description.term
        for description in Description.objects.filter(
            concept__in=codes, type=FULLY_SPECIFIED_NAME
        )
    }


def search(term):
    return set(
        Concept.objects.filter(
            descriptions__term__contains=term, descriptions__active=True, active=True
        ).values_list("id", flat=True)
    )


def ancestor_relationships(codes):
    placeholders = ", ".join(["%s"] * len(codes))
    sql = f"""
    WITH RECURSIVE tree(parent_id, child_id) AS (
      SELECT
        destination_id AS parent_id,
        source_id AS child_id
      FROM snomedct_relationship
      WHERE child_id IN ({placeholders})
        AND type_id = '{IS_A}'
        AND active

      UNION

      SELECT
        r.destination_id AS parent_id,
        r.source_id AS child_id
      FROM snomedct_relationship r
      INNER JOIN tree t
        ON r.source_id = t.parent_id
      WHERE r.type_id = '{IS_A}'
        AND active
    )

    SELECT parent_id, child_id FROM tree
    """

    return query(sql, codes)


def descendant_relationships(codes):
    placeholders = ", ".join(["%s"] * len(codes))
    sql = f"""
    WITH RECURSIVE tree(parent_id, child_id) AS (
      SELECT
        destination_id AS parent_id,
        source_id AS child_id
      FROM snomedct_relationship
      WHERE parent_id IN ({placeholders})
        AND type_id = '{IS_A}'
        AND active

      UNION

      SELECT
        r.destination_id AS parent_id,
        r.source_id AS child_id
      FROM snomedct_relationship r
      INNER JOIN tree t
        ON r.destination_id = t.child_id
      WHERE r.type_id = '{IS_A}'
        AND active
    )

    SELECT parent_id, child_id FROM tree
    """

    return query(sql, codes)
