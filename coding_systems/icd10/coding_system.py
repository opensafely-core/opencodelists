from collections import defaultdict
from functools import lru_cache

from opencodelists.db_utils import query

from .models import Concept

name = "ICD-10"
short_name = "ICD-10"

root = ""


def search_by_term(term):
    return set(
        Concept.objects.filter(kind="category")
        .filter(term__contains=term)
        .values_list("code", flat=True)
    )


def search_by_code(code):
    try:
        concept = Concept.objects.get(code__iexact=code)
    except Concept.ObjectDoesNotExist:
        return set()

    # The UI does not support top-level concepts being included/excluded (and in any
    # case, they cannot appear on a patient record) so if a user searches for a chapter
    # code, we instead return the codes for all children of that chapter.
    if concept.kind == "chapter":
        return {child.code for child in concept.children.all()}
    else:
        return {code}


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
        chapter_code = code_to_chapter()[code]
        chapter_name = chapter_code_to_chapter_name()[chapter_code]
        codes_by_type[chapter_name].append(code)
    return dict(codes_by_type)


@lru_cache()
def code_to_chapter():
    """Return mapping from a concept's code to the code of its chapter.

    Each concept belongs exactly one chapter.

    Concepts are of three types:

        * chapters (I, II, etc)
        * blocks (A00-A09, A15-A19, etc)
        * categories (A00, A01, etc, and also A00.0, A00.1, etc)

    Some blocks are children of chapters, while others are children of other blocks.
    And some categories are children of blocks, while others are children of other
    categories.

    If a block is a child of another block, that parent block will be the child of a
    chapter.  And if a category is a child of another category, that parent category
    will be the child of a block.
    """

    # Start with mappings from chapter code to chapter code.
    code_to_chapter = {
        chapter.code: chapter.code for chapter in Concept.objects.filter(kind="chapter")
    }

    # Add mappings from blocks that are children of chapters.
    for block in Concept.objects.filter(kind="block", parent__kind="chapter"):
        code_to_chapter[block.code] = code_to_chapter[block.parent_id]

    # Add mappings from blocks that are children of other blocks.
    for block in Concept.objects.filter(kind="block", parent__kind="block"):
        code_to_chapter[block.code] = code_to_chapter[block.parent_id]

    # Add mappings from categories that are children of blocks.
    for category in Concept.objects.filter(kind="category", parent__kind="block"):
        code_to_chapter[category.code] = code_to_chapter[category.parent_id]

    # Add mappings from categories that are children of other categories.
    for category in Concept.objects.filter(kind="category", parent__kind="category"):
        code_to_chapter[category.code] = code_to_chapter[category.parent_id]

    assert len(code_to_chapter) == Concept.objects.count()

    return code_to_chapter


@lru_cache()
def chapter_code_to_chapter_name():
    """Return mapping from a chapter code to its name."""

    return {
        concept.code: f"{concept.code}: {concept.term}"
        for concept in Concept.objects.filter(kind="chapter")
    }
