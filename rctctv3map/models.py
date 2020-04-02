from django.db import models


class Mapping(models.Model):
    id = models.UUIDField(primary_key=True)
    v2_concept_id = models.CharField(max_length=5, db_index=True)
    v2_term_id = models.CharField(max_length=2, db_index=True)
    ctv3_term_id = models.CharField(max_length=5, db_index=True)
    ctv3_termtyp = models.CharField(max_length=1)
    ctv3_concept_id = models.CharField(max_length=5, db_index=True)
    use_ctv3_term_id = models.CharField(max_length=5, db_index=True)
    stat = models.CharField(max_length=1)
    map_typ = models.CharField(max_length=3)
    map_status = models.BooleanField()
    effective_date = models.DateField()
    is_assured = models.BooleanField()
