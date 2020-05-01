from functools import lru_cache

from django.db import connection
from django.urls import reverse

from codelists import tree_utils

from .models import ConceptTermMapping

root = "....."


@lru_cache()
def all_edges():
    sql = "SELECT parent_id, child_id FROM ctv3_concepthierarchy"
    return query(sql)


@lru_cache()
def all_paths():
    return tree_utils.edges_to_paths(root, all_edges())


@lru_cache()
def full_tree():
    return tree_utils.paths_to_tree(all_paths())


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


@lru_cache()
def html_tree_highlighting_codes(codes):
    edges = ancestor_relationships(codes) + descendant_relationships(codes)
    paths = tree_utils.edges_to_paths(root, edges)

    included_codes = set()
    for path in paths:
        for node in path:
            included_codes.add(node)

    code_to_name = lookup_names(included_codes)
    paths = [[(code_to_name[code], code) for code in path] for path in paths]

    pruned_tree = tree_utils.paths_to_tree(paths)

    lines = ["<ul>"]

    last_depth = 0
    for (name, code), depth in tree_utils.tree_depth_first(pruned_tree):
        if depth - last_depth == 1:
            lines.append("<ul>")
        else:
            for i in range(last_depth - depth):
                lines.append("</ul>")

        last_depth = depth

        if code in codes:
            color = "blue"
        else:
            color = "black"

        url = reverse("ctv3:concept", args=[code])

        lines.append(
            f'<li><a href="{url}" style="color: {color}">{name}</a> (<code>{code}</code>)</li>'
        )

    lines.append("</ul>")

    return "\n".join(lines)


@lru_cache()
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


@lru_cache()
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


def query(sql, params=None):
    with connection.cursor() as c:
        c.execute(sql, params)
        return c.fetchall()
