from functools import reduce

from django.db.models import Q

from codelists.coding_system import BaseCodingSystem

from .models import Presentation


class CodingSystem(BaseCodingSystem):
    @classmethod
    def code_to_description_map(cls, codes):
        presentations = Presentation.objects.filter(code__in=codes)
        return {p.code: p.name for p in presentations}

    @classmethod
    def codes_from_query(cls, query):
        prefixes = query.splitlines()
        clauses = [Q(code__startswith=prefix) for prefix in prefixes]
        filter_arg = reduce(Q.__or__, clauses[1:], clauses[0])
        return list(Presentation.objects.filter(filter_arg).values_list("code", flat=True))
