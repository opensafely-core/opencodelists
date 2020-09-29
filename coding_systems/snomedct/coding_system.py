import collections
import re

from opencodelists.db_utils import query

from .models import FULLY_SPECIFIED_NAME, IS_A, Concept, Description

name = "SNOMED CT"
short_name = "SNOMED CT"

root = "138875005"


term_and_type_pat = re.compile(r"(^.*) \(([\w/ ]+)\)$")


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
    codes = list(codes)
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
    codes = list(codes)
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


def _iter_code_to_term_and_type(codes: set):
    for code, term in lookup_names(codes).items():
        match = term_and_type_pat.match(term)
        term_and_type = match.groups() if match else (term, "unknown")

        yield code, term_and_type


def code_to_term_and_type(codes):
    codes = set(codes)
    return dict(_iter_code_to_term_and_type(codes))


def code_to_term(codes):
    return {code: term for code, (term, _) in code_to_term_and_type(codes).items()}


def codes_by_type(codes, hierarchy):
    """Group codes by their Type"""
    # create a lookup of code -> type
    code_to_type = {
        code: type for code, (_, type) in code_to_term_and_type(codes).items()
    }

    lookup = collections.defaultdict(list)

    for code in codes:
        type = code_to_type[code]
        lookup[type].append(code)

    return dict(lookup)
