from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Window
from django.db.models.functions import RowNumber
from django.db.models.manager import BaseManager
from django.db.models.query import QuerySet


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
    ASTERISK = "aster"
    NORMAL = "normal"


class RubricKind(models.TextChoices):
    FOOTNOTE = "footnote"
    TEXT = "text"
    CODING_HINT = "coding_hint"
    DEFINITION = "definition"
    INTRODUCTION = "introduction"
    MODIFIERLINK = "modifierlink"
    NOTE = "note"
    EXCLUSION = "exclusion"
    INCLUSION = "inclusion"
    PREFERREDLONG = "preferredlong"
    PREFERRED = "preferred"
    SMALL = "small"
    SMALL2 = "small2"
    SMALL3 = "small3"
    SMALL2PLAIN = "small2plain"


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


class ConceptEditionQuerySet(QuerySet):
    def prioritise_by_edition(self):
        # Give each ConceptEdition a row number based on the edition from which it came,
        # and only select those with row number==1.
        # This relies on the current state of the edition with id "2016"
        # being the preferred source of ConceptEdition-level data (e.g. terms)
        # over the one with id "2019"

        return self.annotate(
            edition_priority=Window(
                expression=RowNumber(),
                partition_by="concept_id",
                order_by="edition_id",
            )
        ).filter(edition_priority=1)


class ConceptEditionManager(BaseManager.from_queryset(ConceptEditionQuerySet)):
    pass


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

    objects = ConceptEditionManager()

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


class ConceptRubricQuerySet(QuerySet):
    def prioritise_by_edition(self):
        return self.annotate(
            edition_priority=Window(
                expression=RowNumber(),
                partition_by=[F("concept_edition__concept_id"), F("kind")],
                order_by="concept_edition__edition_id",
            )
        ).filter(edition_priority=1)


class ConceptRubricManager(BaseManager.from_queryset(ConceptRubricQuerySet)):
    pass


class ConceptRubric(models.Model):
    kind = get_char_choices_field(RubricKind)
    text = models.TextField()
    concept_edition = models.ForeignKey(
        ConceptEdition, on_delete=models.CASCADE, related_name="rubrics"
    )
    objects = ConceptRubricManager()


class ModifierRubric(models.Model):
    kind = get_char_choices_field(RubricKind)
    text = models.TextField()
    concept_edition = models.ForeignKey(
        ConceptEdition, on_delete=models.CASCADE, related_name="modifier_rubrics"
    )


class DaggerAsteriskRelation(models.Model):
    dagger_concept = models.ForeignKey(
        ConceptEdition,
        on_delete=models.CASCADE,
        related_name="asterisk_relations",
        null=True,
        blank=True,
    )
    dagger_code = models.CharField(max_length=255)
    asterisk_concept = models.ForeignKey(
        ConceptEdition,
        on_delete=models.CASCADE,
        related_name="dagger_relations",
        null=True,
        blank=True,
    )
    asterisk_code = models.CharField(max_length=255)

    def clean(self):
        if not (self.dagger_concept or self.asterisk_concept):
            raise ValidationError(
                "at least one dagger/asterisk concept must resolve to a concept edition"
            )

        if (
            self.dagger_concept
            and self.asterisk_concept
            and self.dagger_concept.edition != self.asterisk_concept.edition
        ):
            raise ValidationError(
                "dagger and asterisk concepts must be from same edition"
            )

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="dagger_asterisk_at_least_one_concept",
                condition=(
                    models.Q(dagger_concept__isnull=False)
                    | models.Q(asterisk_concept__isnull=False)
                ),
            ),
            models.UniqueConstraint(
                fields=("dagger_concept", "asterisk_concept"),
                name="dagger_asterisk_uq_together",
                condition=(
                    models.Q(dagger_concept__isnull=False)
                    & models.Q(asterisk_concept__isnull=False)
                ),
            ),
            models.UniqueConstraint(
                fields=("dagger_concept", "asterisk_code"),
                name="dagger_asterisk_uq_unresolved_asterisk",
                condition=(
                    models.Q(dagger_concept__isnull=False)
                    & models.Q(asterisk_concept__isnull=True)
                ),
            ),
            models.UniqueConstraint(
                fields=("dagger_code", "asterisk_concept"),
                name="dagger_asterisk_uq_unresolved_dagger",
                condition=(
                    models.Q(dagger_concept__isnull=True)
                    & models.Q(asterisk_concept__isnull=False)
                ),
            ),
        ]
