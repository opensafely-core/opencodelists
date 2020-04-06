from django.db import models


class Concept(models.Model):
    id = models.CharField(primary_key=True, max_length=18)
    effective_time = models.DateField()
    active = models.BooleanField()
    module = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="+", db_index=False
    )
    definition_status = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="+", db_index=False
    )


class Description(models.Model):
    id = models.CharField(primary_key=True, max_length=18)
    effective_time = models.CharField(max_length=8)
    active = models.BooleanField()
    module = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="+", db_index=False
    )
    concept = models.ForeignKey("Concept", on_delete=models.CASCADE)
    language_code = models.CharField(max_length=3)
    type = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="+", db_index=False
    )
    term = models.CharField(max_length=255)
    case_significance = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="+", db_index=False
    )


class Relationship(models.Model):
    id = models.CharField(primary_key=True, max_length=18)
    effective_time = models.CharField(max_length=8)
    active = models.BooleanField()
    module = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="+", db_index=False
    )
    source = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="destination_relationships"
    )
    destination = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="source_relationships"
    )
    relationship_group = models.CharField(max_length=3)
    type = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="+", db_index=False
    )
    characteristic_type = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="+", db_index=False
    )
    modifier = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="+", db_index=False
    )
