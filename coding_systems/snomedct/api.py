from functools import lru_cache

from django.db import connection
from django.http import JsonResponse

from .models import FULLY_SPECIFIED_NAME, IS_A, STATED_RELATIONSHIP


def concepts(request):
    ids = tuple(sorted((request.GET["concepts"].split(","))))
    include_ancestors = bool(request.GET.get("include_ancestors"))

    concepts = {
        id: {"id": id, "child_ids": set(), "fetched_all_children": True} for id in ids
    }
    child_ids = set()

    for parent_id, child_id in _child_relationships(ids):
        if parent_id not in concepts:
            concepts[parent_id] = {
                "id": parent_id,
                "child_ids": set(),
                "fetched_all_children": True,
            }
        if child_id not in concepts:
            concepts[child_id] = {
                "id": child_id,
                "child_ids": set(),
                "fetched_all_children": True,
            }

        concepts[parent_id]["child_ids"].add(child_id)
        child_ids.add(child_id)

    child_ids = tuple(sorted(set(child_ids)))

    # only do this if len(child_ids) < N
    for parent_id, child_id in _child_relationships(child_ids):
        concepts[parent_id]["child_ids"].add(child_id)
        if child_id not in concepts:
            concepts[child_id] = {
                "id": child_id,
                "child_ids": set(),
                "fetched_all_children": False,
            }

    if include_ancestors:
        for parent_id, child_id in _ancestor_relationships(ids):
            if parent_id not in concepts:
                concepts[parent_id] = {
                    "id": parent_id,
                    "child_ids": set(),
                    "fetched_all_children": False,
                }
            if child_id not in concepts:
                concepts[child_id] = {
                    "id": child_id,
                    "child_ids": set(),
                    "fetched_all_children": False,
                }

            concepts[parent_id]["child_ids"].add(child_id)

    all_ids = tuple(sorted(concepts.keys()))

    for id, term in _descriptions(all_ids):
        concept = concepts[id]
        concept["fully_specified_name"] = term

    _sort_concept_child_ids(concepts)

    json_data = {"concepts": list(concepts.values())}
    response = JsonResponse(json_data, json_dumps_params={"indent": 2})
    return response


def _child_relationships(ids):
    sql = f"""
    SELECT
      destination_id AS parent_id,
      source_id AS child_id
    FROM snomedct_relationship
    WHERE parent_id IN ({{}})
      AND type_id = '{IS_A}'
      AND characteristic_type_id = '{STATED_RELATIONSHIP}'
      AND active
    """.format(
        ", ".join(["%s"] * len(ids))
    )

    return _query(sql, ids)


def _ancestor_relationships(ids):
    sql = f"""
    WITH RECURSIVE tree(parent_id, child_id) AS (
      SELECT
        destination_id AS parent_id,
        source_id AS child_id
      FROM snomedct_relationship
      WHERE child_id IN ({{}})
        AND type_id = '{IS_A}'
        AND characteristic_type_id = '{STATED_RELATIONSHIP}'
        AND active

      UNION

      SELECT
        r.destination_id AS parent_id,
        r.source_id AS child_id
      FROM snomedct_relationship r
      INNER JOIN tree t
        ON r.source_id = t.parent_id
      WHERE r.type_id = '{IS_A}'
        AND r.characteristic_type_id = '{STATED_RELATIONSHIP}'
        AND r.active
    )

    SELECT parent_id, child_id FROM tree
    """.format(
        ", ".join(["%s"] * len(ids))
    )

    return _query(sql, ids)


def _descriptions(ids):
    sql = f"""
    SELECT concept_id, term
    FROM snomedct_description
    WHERE concept_id IN ({{}})
      AND type_id = '{FULLY_SPECIFIED_NAME}'
      AND active
    """.format(
        ", ".join(["%s"] * len(ids))
    )

    return _query(sql, ids)


def _sort_concept_child_ids(concepts):
    for c in concepts.values():
        if c["child_ids"] is None:
            continue
        c["child_ids"] = sorted(
            c["child_ids"], key=lambda id: concepts[id]["fully_specified_name"]
        )


def search(request):
    term = "%" + request.GET["q"] + "%"

    sql = """
    SELECT DISTINCT concept_id
    FROM snomedct_description
    WHERE term LIKE %s
    """

    json_data = {"concepts": [{"id": row[0]} for row in _query(sql, (term,))]}
    response = JsonResponse(json_data, json_dumps_params={"indent": 2})
    return response


@lru_cache()
def _query(sql, params):
    with connection.cursor() as c:
        c.execute(sql, params)
        return c.fetchall()
