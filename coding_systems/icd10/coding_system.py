from collections import defaultdict
from functools import lru_cache

from opencodelists.db_utils import query

from ..base.coding_system_base import BuilderCompatibleCodingSystem
from .models import Concept


class CodingSystem(BuilderCompatibleCodingSystem):
    id = "icd10"
    name = "ICD-10"
    short_name = "ICD-10"
    root = ""
    csv_headers = {
        "code": ["icd_code", "icd10_code", "code", "icd"],
        "term": ["term", "description", "name", "diag_desc"],
    }

    def search_by_term(self, term):
        return set(
            Concept.objects.using(self.database_alias)
            .filter(kind="category")
            .filter(term__contains=term)
            .values_list("code", flat=True)
        )

    def search_by_code(self, code):
        code = code.upper()
        if code.endswith("*"):
            kwargs = {"code__startswith": code.rstrip("*")}
        else:
            kwargs = {"code": code}

        return set(
            Concept.objects.using(self.database_alias)
            .exclude(kind="chapter")
            .filter(**kwargs)
            .values_list("code", flat=True)
        )

    def ancestor_relationships(self, codes):
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

        return query(sql, codes, database=self.database_alias)

    def descendant_relationships(self, codes):
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

        return query(sql, codes, database=self.database_alias)

    def lookup_names(self, codes):
        return dict(
            Concept.objects.using(self.database_alias)
            .filter(code__in=codes)
            .values_list("code", "term")
        )

    def code_to_term(self, codes):
        lookup = self.lookup_names(codes)
        unknown = set(codes) - set(lookup)
        return {**lookup, **{code: "Unknown" for code in unknown}}

    def codes_by_type(self, codes, hierarchy):
        """Return mapping from chapter name to codes in that chapter."""

        codes_by_type = defaultdict(list)
        for code in codes:
            chapter_code = self.code_to_chapter().get(code)
            chapter_name = (
                self.chapter_code_to_chapter_name()[chapter_code]
                if chapter_code
                else "[Unknown]"
            )
            codes_by_type[chapter_name].append(code)
        return dict(codes_by_type)

    @lru_cache
    def code_to_chapter(self):
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
            chapter.code: chapter.code
            for chapter in Concept.objects.using(self.database_alias).filter(
                kind="chapter"
            )
        }

        # Add mappings from blocks that are children of chapters.
        for block in Concept.objects.using(self.database_alias).filter(
            kind="block", parent__kind="chapter"
        ):
            code_to_chapter[block.code] = code_to_chapter[block.parent_id]

        # Add mappings from blocks that are children of other blocks.
        for block in Concept.objects.using(self.database_alias).filter(
            kind="block", parent__kind="block"
        ):
            code_to_chapter[block.code] = code_to_chapter[block.parent_id]

        # Add mappings from categories that are children of blocks.
        for category in Concept.objects.using(self.database_alias).filter(
            kind="category", parent__kind="block"
        ):
            code_to_chapter[category.code] = code_to_chapter[category.parent_id]

        # Add mappings from categories that are children of other categories.
        for category in Concept.objects.using(self.database_alias).filter(
            kind="category", parent__kind="category"
        ):
            code_to_chapter[category.code] = code_to_chapter[category.parent_id]

        assert (
            len(code_to_chapter) == Concept.objects.using(self.database_alias).count()
        )

        return code_to_chapter

    @lru_cache
    def chapter_code_to_chapter_name(self):
        """Return mapping from a chapter code to its name."""

        return {
            concept.code: f"{concept.code}: {concept.term}"
            for concept in Concept.objects.using(self.database_alias).filter(
                kind="chapter"
            )
        }

    def matching_codes(self, codes):
        return set(
            Concept.objects.using(self.database_alias)
            .filter(code__in=codes)
            .values_list("code", flat=True)
        )
