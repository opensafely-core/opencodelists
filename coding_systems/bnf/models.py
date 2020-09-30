from django.db import models

TYPES = [
    "Chapter",
    "Section",
    "Paragraph",
    "Subparagraph",
    "Chemical Substance",
    "Product",
    "Presentation",
]


class Concept(models.Model):
    code = models.CharField(primary_key=True, max_length=15)
    type = models.CharField(max_length=len("Chemical Substance"))
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="children", null=True
    )
