from django.core import serializers
from django.core.management import BaseCommand

from ...models import CORE_METADATA_CONCEPT, IS_A, Concept, Description


class Command(BaseCommand):
    def handle(self, **kwargs):
        concepts = set()
        relationships = []

        core_metadata_concept = Concept.objects.get(pk=CORE_METADATA_CONCEPT)
        is_a = Concept.objects.get(pk=IS_A)
        todo = [core_metadata_concept]

        while todo:
            concept = todo.pop()
            print(concept.id, concept.fully_specified_name)
            concepts.add(concept)

            for rel in concept.source_relationships.filter(type_id=IS_A).select_related(
                "source"
            ):
                relationships.append(rel)

                c = rel.source
                if c not in concepts:
                    todo.append(c)

        todo = [core_metadata_concept, is_a]

        while todo:
            concept = todo.pop()
            concepts.add(concept)

            for rel in concept.destination_relationships.filter(
                type_id=IS_A
            ).select_related("destination"):
                relationships.append(rel)

                c = rel.destination
                if c not in concepts:
                    todo.append(c)

        descriptions = Description.objects.filter(concept__in=concepts)

        records = list(concepts) + relationships + list(descriptions)

        with open("coding_systems/snomedct/fixtures/snomedct.json", "w") as f:
            serializers.serialize("json", records, stream=f, indent=2)
