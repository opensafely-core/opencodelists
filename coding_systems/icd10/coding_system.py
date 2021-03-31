from collections import defaultdict
from functools import lru_cache

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
    """Return mapping from chapter name to codes in that chapter."""

    codes_by_type = defaultdict(list)
    for code in codes:
        chapter_code = category_to_chapter()[code]
        chapter_name = chapter_code_to_chapter_name()[chapter_code]
        codes_by_type[chapter_name].append(code)
    return dict(codes_by_type)


@lru_cache()
def category_to_chapter():
    """Return mapping from a category code to chapter code.

    Each concept belongs exactly one chapter.

    Concepts are of three types:

        * chapters (I, II, etc)
        * blocks (A00-A09, A15-A19, etc)
        * categories (A00, A01, etc, and also A00.0, A00.1, etc)

    We have to look up the mapping from blocks to chapters, but we can calculate what
    block a category belongs to by its prefix (eg A00.0 belongs to A00-A09).
    """

    block_to_chapter = {
        block_concept.code: block_concept.parent_id
        for block_concept in Concept.objects.filter(
            kind="block", parent__kind="chapter"
        )
    }

    category_to_chapter = {}

    for code in Concept.objects.filter(kind="category").values_list("code", flat=True):
        for block in block_to_chapter:
            lower, upper = block.split("-")
            if (lower <= code <= upper) or code.startswith(upper):
                category_to_chapter[code] = block_to_chapter[block]
                break
        else:
            assert False, code

    return category_to_chapter


@lru_cache()
def chapter_code_to_chapter_name():
    """Return mapping from a chapter code to its name."""

    return {
        concept.code: f"{concept.code}: {concept.term}"
        for concept in Concept.objects.filter(kind="chapter")
    }
