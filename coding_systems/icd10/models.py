from django.core.exceptions import ValidationError
from django.db import models


def get_char_choices_field(choices):
    def longest_choice(choices):
        return max(len(c) for c in choices.__dict__ if not c.startswith("_"))

    return models.CharField(max_length=longest_choice(choices), choices=choices)


class ConceptKind(models.TextChoices):
    CHAPTER = "chapter"
    BLOCK = "block"
    CATEGORY = "category"


class ConceptUsage(models.TextChoices):
    DAGGER = "dagger"
    ASTERISK = "asterisk"
    NORMAL = "normal"


class RubricKind(models.TextChoices):
    INCLUSION = "inclusion"
    EXCLUSION = "exclusion"
    NOTE = "note"
    TEXT = "text"


class Edition(models.Model):
    id = models.CharField(primary_key=True, max_length=20)
    version = models.IntegerField()
    year = models.IntegerField()
    source_description = models.CharField(max_length=255)


class Concept(models.Model):
    code = models.CharField(primary_key=True, max_length=7)
    parent = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="children", null=True
    )
    editions = models.ManyToManyField(Edition, through="ConceptEdition")


class ConceptEdition(models.Model):
    concept = models.ForeignKey(
        Concept, on_delete=models.CASCADE, related_name="concept_editions"
    )
    edition = models.ForeignKey(
        Edition, on_delete=models.CASCADE, related_name="concept_editions"
    )
    kind = get_char_choices_field(ConceptKind)
    usage = get_char_choices_field(ConceptUsage)
    term = models.CharField(max_length=255, blank=True)
    term_modifier = models.CharField(max_length=255, blank=True, null=True)
    modifier_position = models.IntegerField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("concept", "edition"), name="concept_edition_uq_together"
            ),
            models.CheckConstraint(
                name="modifier_position_4_or_5",
                condition=models.Q(modifier_position__in=[4, 5]),
            ),
        ]


class ConceptRubric(models.Model):
    kind = get_char_choices_field(RubricKind)
    text = models.TextField()
    concept_edition = models.ForeignKey(
        ConceptEdition, on_delete=models.CASCADE, related_name="rubrics"
    )


class ModifierRubric(models.Model):
    kind = get_char_choices_field(RubricKind)
    text = models.TextField()
    concept_edition = models.ForeignKey(
        ConceptEdition, on_delete=models.CASCADE, related_name="modifier_rubrics"
    )


class DaggerAsteriskRelation(models.Model):
    dagger_concept = models.ForeignKey(
        ConceptEdition, on_delete=models.CASCADE, related_name="asterisk_relations"
    )
    asterisk_concept = models.ForeignKey(
        ConceptEdition, on_delete=models.CASCADE, related_name="dagger_relations"
    )

    def clean(self):
        if self.dagger_concept.edition != self.asterisk_concept.edition:
            raise ValidationError(
                "dagger and asterisk concepts must be from same edition"
            )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("dagger_concept", "asterisk_concept"),
                name="dagger_asterisk_uq_together",
            ),
        ]
