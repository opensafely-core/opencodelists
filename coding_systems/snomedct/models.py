from django.db import models


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
        """Return fully specified name of this concept.

        The FSN is "a term unique among active descriptions in SNOMED CT that names the
        meaning of a concept code in a manner that is intended to be unambiguous and
        stable across multiple contexts".

        For almost every concept, there is exactly one active description whose type is
        FULLY_SPECIFIED_NAME.  However, there are a handful of exceptions, where the
        same concept has FSN descriptions from both the International release and the UK
        extension release.  When this happens, we choose arbitrarily, by taking the
        first.

        Only a handful of concepts have duplicate FSNs, and (as of October 2021) in all
        but two cases the FSNs are identical.
        """

        if self._fully_specified_name is None:
            if "descriptions" in getattr(self, "_prefetched_objects_cache", {}):
                descriptions = [
                    d
                    for d in self._prefetched_objects_cache["descriptions"]
                    if d.active and d.type_id == FULLY_SPECIFIED_NAME
                ]
                self._fully_specified_name = descriptions[0].term

            else:
                self._fully_specified_name = (
                    self.descriptions.filter(active=True, type_id=FULLY_SPECIFIED_NAME)
                    .first()
                    .term
                )

        return self._fully_specified_name

    @fully_specified_name.setter
    def fully_specified_name(self, fully_specified_name):
        self._fully_specified_name = fully_specified_name


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
