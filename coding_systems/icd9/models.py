from django.db import models


class Concept(models.Model):
    code = models.CharField(primary_key=True, max_length=7)
    kind = models.CharField(max_length=len("category"))
    term = models.CharField(max_length=200)
    parent = models.ForeignKey(
        "Concept",
        on_delete=models.CASCADE,
        related_name="children",
        null=True,
    )
