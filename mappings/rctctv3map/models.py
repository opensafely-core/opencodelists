from django.db import models


class Mapping(models.Model):
    id = models.UUIDField(primary_key=True)
    v2_concept_id = models.TextField(db_index=True)
    v2_term_id = models.TextField(db_index=True)
    ctv3_term_id = models.TextField(db_index=True)
    ctv3_termtyp = models.TextField()
    ctv3_concept_id = models.TextField(db_index=True)
    use_ctv3_term_id = models.TextField(db_index=True)
    stat = models.TextField()
    map_typ = models.TextField()
    map_status = models.BooleanField()
    effective_date = models.DateField()
    is_assured = models.BooleanField()
