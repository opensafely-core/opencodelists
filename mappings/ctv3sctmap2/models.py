from django.db import models

from coding_systems import ctv3, snomedct


class Mapping(models.Model):
    id = models.UUIDField(primary_key=True)
    ctv3_concept = models.ForeignKey(
        ctv3.models.Concept,
        db_constraint=False,
        on_delete=models.PROTECT,
        related_name="snomedct_mappings",
    )
    ctv3_term = models.ForeignKey(
        ctv3.models.Term,
        db_constraint=False,
        on_delete=models.PROTECT,
        related_name="snomedct_mappings",
    )
    ctv3_term_type = models.CharField(max_length=1)
    sct_concept = models.ForeignKey(
        snomedct.models.Concept,
        db_constraint=False,
        null=True,
        on_delete=models.PROTECT,
        related_name="ctv3_mappings",
    )
    sct_description = models.ForeignKey(
        snomedct.models.Description,
        db_constraint=False,
        null=True,
        on_delete=models.PROTECT,
        related_name="ctv3_mappings",
    )
    map_status = models.BooleanField()
    effective_date = models.DateField()
    is_assured = models.BooleanField()
