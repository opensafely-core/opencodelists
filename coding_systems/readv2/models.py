from django.db import models


class Concept(models.Model):
    read_code = models.CharField(primary_key=True, max_length=5)
    name_1 = models.CharField(max_length=30)
    name_2 = models.CharField(max_length=60)
    name_3 = models.CharField(max_length=198)
    unknown_field_4 = models.CharField(max_length=15)  # Probably ICD9_CODE
    unknown_field_5 = models.CharField(max_length=2)  # Probably ICD9_CODE_DEF
    unknown_field_6 = models.CharField(max_length=13)  # Probably ICD9_CM_CODE
    unknown_field_7 = models.CharField(max_length=2)  # Probably ICD9_CM_CODE_DEF
    unknown_field_8 = models.CharField(max_length=19)  # Probably OPSC_CODE
    unknown_field_9 = models.CharField(max_length=2)  # Probably OPSC_CODE_DEF
    speciality_flags = models.CharField(max_length=10)
    status = models.CharField(max_length=1)
    language = models.CharField(max_length=2)
