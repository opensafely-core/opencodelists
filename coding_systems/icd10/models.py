from django.db import models


class Edition(models.Model):
    id = models.CharField(primary_key=True, max_length=20)
    version = models.IntegerField()
    year = models.IntegerField()
    source_description = models.CharField(max_length=255)


class ConceptKind(models.TextChoices):
    CHAPTER = "chapter"
    BLOCK = "block"
    CATEGORY = "category"


class Concept(models.Model):
    code = models.CharField(primary_key=True, max_length=7)
    kind = models.CharField(max_length=len("category"), choices=ConceptKind)
    term = models.CharField(max_length=200)
    parent = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="children", null=True
    )
    modifier_4 = models.CharField(max_length=200, blank=True, null=True)
    modifier_5 = models.CharField(max_length=200, blank=True, null=True)
    editions = models.ManyToManyField(Edition)


class RubricKind(models.TextChoices):
    INCLUSION = "inclusion"
    EXCLUSION = "exclusion"
    NOTE = "note"
    TEXT = "text"


class Rubric(models.Model):
    kind = models.CharField(max_length=len("exclusion"), choices=RubricKind.choices)
    text = models.TextField()
    concept = models.ForeignKey(
        Concept, on_delete=models.CASCADE, related_name="rubrics"
    )


class ConceptEdition(models.Model):
    concept = models.ForeignKey(
        Concept, on_delete=models.CASCADE, related_name="concepts"
    )
    edition = models.ForeignKey(
        Edition, on_delete=models.CASCADE, related_name="editions"
    )
    term = models.CharField(max_length=200, blank=True)
    modifier_4 = models.CharField(max_length=200, blank=True, null=True)
    modifier_5 = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("concept", "edition"), name="concept_edition_uq_together"
            )
        ]
