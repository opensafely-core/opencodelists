from collections import defaultdict
from functools import lru_cache

from opencodelists.db_utils import query

from ..base.coding_system_base import BuilderCompatibleCodingSystem
from .models import Concept, ConceptEdition, ConceptKind, Edition


class CodingSystem(BuilderCompatibleCodingSystem):
    id = "icd10"
    name = "ICD-10"
    short_name = "ICD-10"
    description = "Internationally standardised diagnosis codes (mainly Secondary Care and Death Registry)"
    root = ""
    csv_headers = {
        "code": ["icd_code", "icd10_code", "code", "icd"],
        "term": ["term", "description", "name", "diag_desc"],
    }
    sort_by_term = False

    def __init__(self, database_alias):
        super().__init__(database_alias)
        self.latest_edition = (
            Edition.objects.using(self.database_alias).order_by("-year").first()
        )

    def search_by_term(self, term):
        return set(
            ConceptEdition.objects.using(self.database_alias)
            .filter(kind=ConceptKind.CATEGORY)
            .filter(term__contains=term)
            .values_list("concept__code", flat=True)
        )

    def search_by_code(self, code):
        code = code.upper()
        if code.endswith("*"):
            kwargs = {"concept__code__startswith": code.rstrip("*")}
        else:
            kwargs = {"concept__code": code}

        return set(
            ConceptEdition.objects.using(self.database_alias)
            .exclude(kind=ConceptKind.CHAPTER)
            .filter(**kwargs)
            .values_list("concept__code", flat=True)
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
        lookup = {}
        concepts = (
            ConceptEdition.objects.using(self.database_alias)
            .filter(concept_id__in=codes)
            .order_by("concept_id", "-edition__year", "-edition__version")
            .values_list("concept_id", "term", "term_modifier")
        )

        for concept_id, term, term_modifier in concepts:
            lookup.setdefault(
                concept_id, f"{term} : {term_modifier}" if term_modifier else term
            )

        return lookup

    def code_to_term(self, codes):
        lookup = self.lookup_names(codes)
        unknown = set(codes) - set(lookup)
        return {**lookup, **{code: "Unknown" for code in unknown}}

    def codes_by_type(self, codes, hierarchy):
        """Return mapping from chapter name to codes in that chapter."""

        codes_by_type = defaultdict(list)
        for code in codes:
            chapter_code = self._code_to_chapter().get(code)
            chapter_name = (
                self._chapter_code_to_chapter_name()[chapter_code]
                if chapter_code
                else "[Unknown]"
            )
            codes_by_type[chapter_name].append(code)
        return dict(codes_by_type)

    @lru_cache
    def _code_to_chapter(self):
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

        concept_rows = list(
            ConceptEdition.objects.using(self.database_alias)
            .order_by("concept_id", "-edition__year", "-edition__version")
            .values_list("concept_id", "concept__parent_id", "kind")
        )

        parent_by_code = {code: parent_code for code, parent_code, _ in concept_rows}
        kind_by_code = {code: kind for code, _, kind in concept_rows}
        code_to_chapter = {
            code: code for code, _, kind in concept_rows if kind == ConceptKind.CHAPTER
        }

        def chapter_for(code):
            if code in code_to_chapter:
                return code_to_chapter[code]

            parent_code = parent_by_code.get(code)
            chapter_code = chapter_for(parent_code)
            code_to_chapter[code] = chapter_code
            return chapter_code

        for code, kind in kind_by_code.items():
            if kind in (ConceptKind.BLOCK, ConceptKind.CATEGORY):
                chapter_for(code)

        return code_to_chapter

    @lru_cache
    def _chapter_code_to_chapter_name(self):
        """Return mapping from a chapter code to its name."""

        return {
            conceptedition.concept.code: f"{conceptedition.concept.code}: {conceptedition.term}"
            for conceptedition in ConceptEdition.objects.using(
                self.database_alias
            ).filter(edition=self.latest_edition, kind=ConceptKind.CHAPTER)
        }

    def matching_codes(self, codes):
        return set(
            Concept.objects.using(self.database_alias)
            .filter(code__in=codes)
            .values_list("code", flat=True)
        )
