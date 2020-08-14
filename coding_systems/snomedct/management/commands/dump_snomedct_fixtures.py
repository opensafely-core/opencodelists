"""
Generate a JSON fixture containing every Concept related to the given Concepts via an
IS_A relationship.  Additionally includes every Description and IS_A Relationship for
these Concepts.

The generated fixture can be loaded with `loaddata`.
"""
from django.core import serializers
from django.core.management import BaseCommand

from ...models import IS_A, Concept, Description


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument("codes", nargs="+", help="Codes of concepts to start from")
        parser.add_argument("--path", help="Path to write fixture to")

    def handle(self, path, codes, **kwargs):
        starting_concepts = Concept.objects.filter(pk__in=codes)
        assert len(codes) == starting_concepts.count()
        concepts = set()
        relationships = set()

        # Walk up the hierarchy, collecting concepts and relationships
        todo = list(starting_concepts)

        while todo:
            concept = todo.pop()
            print(concept.id, concept.fully_specified_name)
            concepts.add(concept)

            for rel in concept.source_relationships.filter(type_id=IS_A).select_related(
                "source"
            ):
                relationships.add(rel)

                c = rel.source
                if c not in concepts:
                    todo.append(c)

        # Walk down the hierarchy
        todo = list(starting_concepts)

        while todo:
            concept = todo.pop()
            print(concept.id, concept.fully_specified_name)
            concepts.add(concept)

            for rel in concept.destination_relationships.filter(
                type_id=IS_A
            ).select_related("destination"):
                relationships.add(rel)

                c = rel.destination
                if c not in concepts:
                    todo.append(c)

        descriptions = Description.objects.filter(concept__in=concepts)

        print(f"{len(concepts)} concepts")
        print(f"{len(relationships)} relationships")
        print(f"{len(descriptions)} descriptions")

        records = list(concepts) + list(relationships) + list(descriptions)

        with open(path, "w") as f:
            serializers.serialize("json", records, stream=f, indent=2)
