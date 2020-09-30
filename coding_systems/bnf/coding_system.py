from collections import defaultdict

from django.db.models import Q

from opencodelists.db_utils import query

from .models import Concept

name = "Pseudo BNF"
short_name = "BNF"

root = ""


def search(term):
    return set(
        Concept.objects.filter(Q(name__contains=term) | Q(code=term)).values_list(
            "code", flat=True
        )
    )


def ancestor_relationships(codes):
    codes = list(codes)
    concept_table = Concept._meta.db_table
    placeholders = ", ".join(["%s"] * len(codes))
    sql = f"""
    WITH RECURSIVE tree(parent_code, child_code) AS (
      SELECT parent_id AS parent_code, code AS child_code
      FROM {concept_table}
      WHERE code IN ({placeholders}) AND parent_id

      UNION

      SELECT c.parent_id AS parent_code, c.code AS child_code
      FROM {concept_table} c
      INNER JOIN tree t
        ON c.code = t.parent_code
    )

    SELECT parent_code, child_code FROM tree
    """

    return query(sql, codes)


def descendant_relationships(codes):
    codes = list(codes)
    concept_table = Concept._meta.db_table
    placeholders = ", ".join(["%s"] * len(codes))
    sql = f"""
    WITH RECURSIVE tree(parent_code, child_code) AS (
      SELECT parent_id AS parent_code, code AS child_code
      FROM {concept_table}
      WHERE parent_code IN ({placeholders})

      UNION

      SELECT c.parent_id AS parent_code, c.code AS child_code
      FROM {concept_table} c
      INNER JOIN tree t
        ON c.parent_id = t.child_code
    )

    SELECT parent_code, child_code FROM tree
    """

    return query(sql, codes)


def code_to_term(codes):
    return dict(Concept.objects.filter(code__in=codes).values_list("code", "name"))


def codes_by_type(codes, hierarchy):
    codes_by_chapter = defaultdict(list)
    for code in codes:
        codes_by_chapter[code[:2]].append(code)

    prefix_to_chapter_name = dict(
        Concept.objects.filter(type="Chapter", code__in=codes_by_chapter).values_list(
            "code", "name"
        )
    )

    return {
        f"Chapter {chapter_code}: {prefix_to_chapter_name[chapter_code]}": codes
        for chapter_code, codes in codes_by_chapter.items()
    }
