from django.db import models


class Mapping(models.Model):
    id = models.CharField(primary_key=True, max_length=18)
    vpidprev = models.CharField(max_length=18)
