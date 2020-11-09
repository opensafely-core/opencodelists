from django.db import models


class Mapping(models.Model):
    dmd_code = models.CharField(primary_key=True, max_length=18)
    dmd_type = models.CharField(max_length=4)
    bnf_concept = models.ForeignKey(
        "bnf.Concept",
        db_constraint=False,
        on_delete=models.PROTECT,
        related_name="bnf_mappings",
    )
