from django.db import models


class Concept(models.Model):
    read_code = models.CharField(primary_key=True, max_length=5)
    unknown_field_1 = models.CharField(max_length=1)
    unknown_field_2 = models.CharField(max_length=1)
    another_concept = models.ForeignKey("Concept", on_delete=models.CASCADE)
    children = models.ManyToManyField(
        "self",
        through="ConceptHierarchy",
        through_fields=("parent", "child"),
        symmetrical=False,
        related_name="parents",
    )
    terms = models.ManyToManyField(
        "Term", through="ConceptTermMapping", related_name="concepts",
    )

    def all_terms(self):
        assert "terms" in self._prefetched_objects_cache
        return self.terms.all()


class ConceptHierarchy(models.Model):
    parent = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="parent_links"
    )
    child = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="child_links"
    )
    unknown_field_3 = models.CharField(max_length=2)


class Term(models.Model):
    term_id = models.CharField(primary_key=True, max_length=5)
    unknown_field_4 = models.CharField(max_length=1)
    name_1 = models.CharField(max_length=30)
    name_2 = models.CharField(max_length=60, null=True)
    name_3 = models.CharField(max_length=198, null=True)

    def name(self):
        return self.name_3 or self.name_2 or self.name_1


class ConceptTermMapping(models.Model):
    concept = models.ForeignKey("Concept", on_delete=models.CASCADE)
    term = models.ForeignKey("Term", on_delete=models.CASCADE)
    unknown_field_5 = models.CharField(max_length=1)
