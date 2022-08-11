from django.db import models


class Mapping(models.Model):
    """
    Mappings between CTV3 and SNOMED CT Concepts.

    NHS Digital has published mappings between Concepts in the CTV3 and SNOMED CT
    coding systems [1].  We ingest those mappings and store them with this
    model.

    1: https://isd.digital.nhs.uk/trud3/user/authenticated/group/0/pack/8/subpack/9/releases
    """

    id = models.UUIDField(primary_key=True)
    ctv3_concept = models.ForeignKey(
        "ctv3.RawConcept",
        db_constraint=False,
        on_delete=models.PROTECT,
        related_name="snomedct_mappings",
    )
    ctv3_term = models.ForeignKey(
        "ctv3.RawTerm",
        db_constraint=False,
        on_delete=models.PROTECT,
        related_name="snomedct_mappings",
    )
    ctv3_term_type = models.CharField(max_length=1)
    sct_concept = models.ForeignKey(
        "snomedct.Concept",
        db_constraint=False,
        null=True,
        on_delete=models.PROTECT,
        related_name="ctv3_mappings",
    )
    sct_description = models.ForeignKey(
        "snomedct.Description",
        db_constraint=False,
        null=True,
        on_delete=models.PROTECT,
        related_name="ctv3_mappings",
    )
    map_status = models.BooleanField()
    effective_date = models.DateField()
    is_assured = models.BooleanField()
