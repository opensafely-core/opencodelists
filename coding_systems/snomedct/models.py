from django.db import models
from django.db.models import F

# Magic numbers
ROOT_CONCEPT = "138875005"

FULLY_SPECIFIED_NAME = "900000000000003001"
SYNONYM = "900000000000013009"

IS_A = "116680003"

STATED_RELATIONSHIP = "900000000000010007"
INFERRED_RELATIONSHIP = "900000000000011006"
ADDITIONAL_RELATIONSHIP = "900000000000227009"


class Concept(models.Model):
    _fully_specified_name = None
    _synonyms = None

    id = models.CharField(primary_key=True, max_length=18)
    effective_time = models.DateField()
    active = models.BooleanField()
    module = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="+", db_index=False
    )
    definition_status = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="+", db_index=False
    )
    sources = models.ManyToManyField(
        "self",
        through="Relationship",
        through_fields=("destination", "source"),
        symmetrical=False,
        related_name="destinations",
    )

    @property
    def fully_specified_name(self):
        if self._fully_specified_name is None:
            if "descriptions" in getattr(self, "_prefetched_objects_cache", {}):
                descriptions = [
                    d
                    for d in self._prefetched_objects_cache["descriptions"]
                    if d.active and d.type_id == FULLY_SPECIFIED_NAME
                ]
                assert len(descriptions) == 1
                self._fully_specified_name = descriptions[0].term

            else:
                self._fully_specified_name = (
                    self.descriptions.filter(active=True, type_id=FULLY_SPECIFIED_NAME)
                    .get()
                    .term
                )

        return self._fully_specified_name

    @fully_specified_name.setter
    def fully_specified_name(self, fully_specified_name):
        self._fully_specified_name = fully_specified_name

    @property
    def synonyms(self):
        if self._synonyms is None:
            if "descriptions" in getattr(self, "_prefetched_objects_cache", {}):
                self._synonyms = [
                    d.term
                    for d in self._prefetched_objects_cache["descriptions"]
                    if d.active and d.type_id == SYNONYM
                ]

            else:
                self._synonyms = [
                    d.term
                    for d in self.descriptions.filter(active=True, type_id=SYNONYM)
                ]

        return self._synonyms

    @synonyms.setter
    def synonyms(self, synonyms):
        self._synonyms = synonyms

    def parents(self, relationship_types):
        return self.destinations.filter(
            source_relationships__active=True,
            source_relationships__type_id=IS_A,
            source_relationships__characteristic_type_id__in=relationship_types,
            source_relationships__destination__descriptions__active=True,
            source_relationships__destination__descriptions__type_id=FULLY_SPECIFIED_NAME,
        ).annotate(
            fully_specified_name=F(
                "source_relationships__destination__descriptions__term"
            )
        ).distinct()

    def children(self, relationship_types):
        return self.sources.filter(
            destination_relationships__active=True,
            destination_relationships__type_id=IS_A,
            destination_relationships__characteristic_type_id__in=relationship_types,
            destination_relationships__source__descriptions__active=True,
            destination_relationships__source__descriptions__type_id=FULLY_SPECIFIED_NAME,
        ).annotate(
            fully_specified_name=F(
                "destination_relationships__source__descriptions__term"
            )
        ).distinct()


class Description(models.Model):
    id = models.CharField(primary_key=True, max_length=18)
    effective_time = models.CharField(max_length=8)
    active = models.BooleanField()
    module = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="+", db_index=False
    )
    concept = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="descriptions"
    )
    language_code = models.CharField(max_length=3)
    type = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="+", db_index=False
    )
    term = models.CharField(max_length=255)
    case_significance = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="+", db_index=False
    )


class Relationship(models.Model):
    id = models.CharField(primary_key=True, max_length=18)
    effective_time = models.CharField(max_length=8)
    active = models.BooleanField()
    module = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="+", db_index=False
    )
    source = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="destination_relationships"
    )
    destination = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="source_relationships"
    )
    relationship_group = models.CharField(max_length=3)
    type = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="+", db_index=False
    )
    characteristic_type = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="+", db_index=False
    )
    modifier = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="+", db_index=False
    )
