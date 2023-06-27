from collections import defaultdict

from opencodelists.db_utils import query

from ..base.coding_system_base import BaseCodingSystem
from .models import Concept


class CodingSystem(BaseCodingSystem):
    id = "bnf"
    name = "Pseudo BNF"
    short_name = "BNF"
    root = ""
    csv_headers = {
        "code": ["code"],
        "term": ["term", "description"],
    }

    def search_by_term(self, term):
        return set(
            Concept.objects.using(self.database_alias)
            .filter(name__contains=term)
            .values_list("code", flat=True)
        )

    def search_by_code(self, code):
        try:
            concept = Concept.objects.using(self.database_alias).get(code__iexact=code)
        except Concept.DoesNotExist:
            return set()

        # The UI does not support top-level concepts being included/excluded (and in any
        # case, they cannot appear on a patient record) so if a user searches for a chapter
        # code, we instead return the codes for all children of that chapter.
        if concept.type == "Chapter":
            return {child.code for child in concept.children.all()}
        else:
            return {code}

    def matching_codes(self, codes):
        return set(
            Concept.objects.using(self.database_alias)
            .filter(code__in=codes)
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
            .values_list("code", "name")
        )

    def code_to_term(self, codes):
        lookup = self.lookup_names(codes)
        unknown = set(codes) - set(lookup)
        return {**lookup, **{code: "Unknown" for code in unknown}}

    def codes_by_type(self, codes, hierarchy):
        codes_by_chapter = defaultdict(list)
        for code in codes:
            codes_by_chapter[code[:2]].append(code)

        prefix_to_chapter_name = dict(
            Concept.objects.using(self.database_alias)
            .filter(type="Chapter", code__in=codes_by_chapter)
            .values_list("code", "name")
        )

        return {
            f"Chapter {chapter_code}: {prefix_to_chapter_name.get(chapter_code, '[Unknown]')}": codes
            for chapter_code, codes in codes_by_chapter.items()
        }
