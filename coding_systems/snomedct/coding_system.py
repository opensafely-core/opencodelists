import collections
import re

from opencodelists.db_utils import query

from ..base.coding_system_base import BaseCodingSystem
from .models import FULLY_SPECIFIED_NAME, IS_A, Concept, Description


term_and_type_pat = re.compile(r"(^.*) \(([\w/ ]+)\)$")


class CodingSystem(BaseCodingSystem):
    id = "snomedct"
    name = "SNOMED CT"
    short_name = "SNOMED CT"
    root = "138875005"
    csv_headers = {
        "code": ["code", "id", "snomedcode", "dmd_id"],
        "term": ["term", "long_name", "name", "ethnicity", "dmd_name"],
    }

    def lookup_names(self, codes):
        return {
            description.concept_id: description.term
            for description in Description.objects.using(self.database_alias).filter(
                concept__in=codes, type=FULLY_SPECIFIED_NAME, active=True
            )
        }

    def search_by_term(self, term):
        return set(
            Concept.objects.using(self.database_alias)
            .filter(descriptions__term__contains=term, descriptions__active=True)
            .values_list("id", flat=True)
        )

    def search_by_code(self, code):
        if Concept.objects.using(self.database_alias).filter(id=code).exists():
            return {code}
        else:
            return set()

    def matching_codes(self, codes):
        return set(
            Concept.objects.using(self.database_alias)
            .filter(id__in=codes)
            .values_list("id", flat=True)
        )

    def ancestor_relationships(self, codes):
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

        return query(sql, codes, database=self.database_alias)

    def descendant_relationships(self, codes):
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

        return query(sql, codes, database=self.database_alias)

    def _iter_code_to_term_and_type(self, codes: set):
        for code, term in self.lookup_names(codes).items():
            match = term_and_type_pat.match(term)
            term_and_type = match.groups() if match else (term, "unknown")

            yield code, term_and_type

    def code_to_term_and_type(self, codes):
        codes = set(codes)
        return dict(self._iter_code_to_term_and_type(codes))

    def code_to_term(self, codes):
        lookup = {
            code: term for code, (term, _) in self.code_to_term_and_type(codes).items()
        }
        unknown = set(codes) - set(lookup)
        return {**lookup, **{code: "Unknown" for code in unknown}}

    def codes_by_type(self, codes, hierarchy):
        """Group codes by their Type"""
        # create a lookup of code -> type
        code_to_type = {
            code: type.title()
            for code, (_, type) in self.code_to_term_and_type(codes).items()
        }

        code_to_active = {
            concept.id: concept.active
            for concept in Concept.objects.using(self.database_alias).filter(
                id__in=codes
            )
        }

        lookup = collections.defaultdict(list)

        for code in codes:
            type = code_to_type.get(code)
            if type is None:
                lookup["[unknown]"].append(code)
            elif code_to_active[code]:
                lookup[type].append(code)
            else:
                lookup[f"[inactive] {type}"].append(code)

        return dict(lookup)
