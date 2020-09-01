from django.db import models
from django.db.models import OuterRef, Subquery

from mappings.ctv3sctmap2.models import Mapping

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
    _in_ctv3 = None

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

    @property
    def in_ctv3(self):
        if self._in_ctv3 is None:
            self._in_ctv3 = self.ctv3_mappings.exists()

        return self._in_ctv3

    @in_ctv3.setter
    def in_ctv3(self, in_ctv3):
        self._in_ctv3 = bool(in_ctv3)

    @property
    def parents(self):
        descriptions = Description.objects.filter(
            concept=OuterRef("source_relationships__destination_id"),
            active=True,
            type_id=FULLY_SPECIFIED_NAME,
        ).values("term")

        mappings = Mapping.objects.filter(
            sct_concept=OuterRef("source_relationships__source_id")
        ).values("id")[:1]

        return (
            (
                self.destinations.filter(
                    source_relationships__active=True,
                    source_relationships__type_id=IS_A,
                )
            )
            .annotate(
                fully_specified_name=Subquery(descriptions), in_ctv3=Subquery(mappings)
            )
            .distinct()
        )

    @property
    def children(self):
        descriptions = Description.objects.filter(
            concept=OuterRef("destination_relationships__source_id"),
            active=True,
            type_id=FULLY_SPECIFIED_NAME,
        ).values("term")

        mappings = Mapping.objects.filter(
            sct_concept=OuterRef("destination_relationships__source_id")
        ).values("id")[:1]

        return (
            self.sources.filter(
                destination_relationships__active=True,
                destination_relationships__type_id=IS_A,
            )
            .annotate(
                fully_specified_name=Subquery(descriptions), in_ctv3=Subquery(mappings)
            )
            .distinct()
        )


class Description(models.Model):
    id = models.CharField(primary_key=True, max_length=18)
    effective_time = models.DateField()
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
    effective_time = models.DateField()
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


class HistorySubstitution(models.Model):
    old_concept = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="+", db_constraint=False
    )
    old_concept_status = models.CharField(max_length=18)
    new_concept = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="+", db_constraint=False
    )
    new_concept_status = models.CharField(max_length=18)
    path = models.CharField(max_length=255)
    is_ambiguous = models.BooleanField()
    iterations = models.IntegerField()
    old_concept_fsn = models.CharField(max_length=255)
    old_concept_fsn_tagcount = models.IntegerField()
    new_concept_fsn = models.CharField(max_length=255)
    new_concept_fsn_tagcount = models.IntegerField()
    tlh_identical_flag = models.BooleanField()
    fsn_tagless_identical_flag = models.BooleanField()
    fsn_tag_identical_flag = models.BooleanField()


class QueryTableRecord(models.Model):
    supertype = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="+", db_constraint=False
    )
    subtype = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="+", db_constraint=False
    )
    provenance = models.IntegerField()
