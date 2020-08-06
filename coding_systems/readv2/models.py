from django.db import models


class Concept(models.Model):
    read_code = models.TextField(primary_key=True)
    name_1 = models.TextField()
    name_2 = models.TextField()
    name_3 = models.TextField()
    unknown_field_4 = models.TextField()  # Probably ICD9_CODE
    unknown_field_5 = models.TextField()  # Probably ICD9_CODE_DEF
    unknown_field_6 = models.TextField()  # Probably ICD9_CM_CODE
    unknown_field_7 = models.TextField()  # Probably ICD9_CM_CODE_DEF
    unknown_field_8 = models.TextField()  # Probably OPSC_CODE
    unknown_field_9 = models.TextField()  # Probably OPSC_CODE_DEF
    speciality_flags = models.TextField()
    status = models.TextField()
    language = models.TextField()
