from django.db import models


class Concept(models.Model):
    STATUS_C = "C"
    STATUS_E = "E"
    STATUS_O = "O"
    STATUS_R = "R"
    STATUS_CHOICES = [
        (STATUS_C, "Current"),
        (STATUS_E, "Extinct"),
        (STATUS_O, "Optional"),
        (STATUS_R, "Redundant"),
    ]

    UNKNOWN_FIELD_2_A = "A"
    UNKNOWN_FIELD_2_N = "N"
    UNKNOWN_FIELD_2_CHOICES = [
        (UNKNOWN_FIELD_2_A, "Unknown field 2: A"),
        (UNKNOWN_FIELD_2_A, "Unknown field 2: N"),
    ]

    read_code = models.CharField(primary_key=True, max_length=5)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    unknown_field_2 = models.CharField(max_length=1, choices=UNKNOWN_FIELD_2_CHOICES)
    another_concept = models.ForeignKey("Concept", on_delete=models.CASCADE)
    children = models.ManyToManyField(
        "self",
        through="ConceptHierarchy",
        through_fields=("parent", "child"),
        symmetrical=False,
        related_name="parents",
    )
    terms = models.ManyToManyField(
        "Term", through="ConceptTermMapping", related_name="concepts"
    )

    def all_terms(self):
        assert "terms" in self._prefetched_objects_cache
        return self.terms.all()

    def preferred_term(self):
        return (
            self.terms.filter(
                concepttermmapping__term_type=ConceptTermMapping.PREFERRED
            )
            .get()
            .name()
        )

    def synonyms(self):
        return sorted(
            term.name()
            for term in self.terms.exclude(
                concepttermmapping__term_type=ConceptTermMapping.PREFERRED
            )
        )


class ConceptHierarchy(models.Model):
    parent = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="child_links"
    )
    child = models.ForeignKey(
        "Concept", on_delete=models.CASCADE, related_name="parent_links"
    )
    list_order = models.CharField(max_length=2)


class Term(models.Model):
    STATUS_C = "C"
    STATUS_O = "O"
    STATUS_CHOICES = [
        (STATUS_C, "Status: C (Current?)"),
        (STATUS_O, "Status: O (Optional?)"),
    ]

    term_id = models.CharField(primary_key=True, max_length=5)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    name_1 = models.CharField(max_length=30)
    name_2 = models.CharField(max_length=60, null=True)
    name_3 = models.CharField(max_length=198, null=True)

    def name(self):
        return self.name_3 or self.name_2 or self.name_1


class ConceptTermMapping(models.Model):
    PREFERRED = "P"
    SYNONYM = "S"
    TERM_TYPE_CHOICES = [
        (PREFERRED, "Preferred"),
        (SYNONYM, "Synonym"),
    ]

    concept = models.ForeignKey("Concept", on_delete=models.CASCADE)
    term = models.ForeignKey("Term", on_delete=models.CASCADE)
    term_type = models.CharField(max_length=1, choices=TERM_TYPE_CHOICES)
