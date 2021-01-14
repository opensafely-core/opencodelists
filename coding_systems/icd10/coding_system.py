from collections import defaultdict

from django.db.models import Q

from opencodelists.db_utils import query

from .models import Concept

name = "ICD-10"
short_name = "ICD-10"

root = ""


def search(term):
    return set(
        Concept.objects.filter(kind="category")
        .filter(Q(term__contains=term) | Q(code=term))
        .values_list("code", flat=True)
    )


def ancestor_relationships(codes):
    codes = list(codes)
    concept_table = Concept._meta.db_table
    placeholders = ", ".join(["%s"] * len(codes))
    sql = f"""
    WITH RECURSIVE tree(parent_code, child_code) AS (
      SELECT parent_id AS parent_code, code AS child_code
      FROM {concept_table}
      WHERE code IN ({placeholders}) AND parent_id IS NOT NULL

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
    return dict(Concept.objects.filter(code__in=codes).values_list("code", "term"))


lookup_names = code_to_term


def codes_by_type(codes, hierarchy):
    """Return mapping from a chapter name (ICD-10 types) to those codes in that chapter.

    Each concept belongs exactly one chapter.

    Concepts are of three types:

        * chapters (I, II, etc)
        * blocks (A00-A09, A15-A19, etc)
        * categories (A00, A01, etc, and also A00.0, A00.1, etc)

    We have to look up the mapping from blocks to chapters, but we can calculate what
    block a category belongs to by its prefix (eg A00.0 belongs to A00-A09).
    """

    block_code_to_chapter_code = {
        block_concept.code: block_concept.parent_id
        for block_concept in Concept.objects.filter(kind="block")
    }
    chapter_codes = set(block_code_to_chapter_code.values())

    codes_by_chapter_code = defaultdict(list)

    for code in codes:
        if code in chapter_codes:
            codes_by_chapter_code[code].append(code)
        elif code in block_code_to_chapter_code:
            codes_by_chapter_code[block_code_to_chapter_code[code]].append(code)
        else:
            for block_code in block_code_to_chapter_code:
                lower, upper = block_code.split("-")
                if lower <= code <= upper:
                    codes_by_chapter_code[
                        block_code_to_chapter_code[block_code]
                    ].append(code)
                    break
            else:
                assert False, code

    chapter_code_to_chapter_name = dict(
        Concept.objects.filter(
            kind="chapter", code__in=codes_by_chapter_code
        ).values_list("code", "term")
    )

    return {
        f"{chapter_code}: {chapter_code_to_chapter_name[chapter_code]}": codes
        for chapter_code, codes in codes_by_chapter_code.items()
    }
