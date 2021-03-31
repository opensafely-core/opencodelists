"""
Generate a JSON fixture containing every Concept related to Concepts with given codes.

The generated fixture can be loaded with `loaddata`.
"""
from operator import attrgetter

from django.core import serializers
from django.core.management import BaseCommand

from ...models import Concept


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument("codes", nargs="+", help="Codes of concepts to start from")
        parser.add_argument("--path", help="Path to write fixture to")

    def handle(self, path, codes, **kwargs):
        starting_concepts = Concept.objects.filter(pk__in=codes)
        assert len(codes) == starting_concepts.count()
        concepts = set()

        # Walk up the hierarchy
        todo = list(starting_concepts)

        while todo:
            concept = todo.pop()
            print(concept.code, concept.term)
            concepts.add(concept)

            if concept.parent is not None:
                todo.append(concept.parent)

        # Walk down the hierarchy
        todo = list(starting_concepts)

        while todo:
            concept = todo.pop()
            print(concept.code, concept.term)
            concepts.add(concept)

            todo.extend(concept.children.all())

        concepts = sorted(concepts, key=attrgetter("pk"))

        with open(path, "w") as f:
            serializers.serialize("json", concepts, stream=f, indent=2)
