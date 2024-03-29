from django.db import models


class RawConcept(models.Model):
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
    another_concept = models.ForeignKey("RawConcept", on_delete=models.CASCADE)
    children = models.ManyToManyField(
        "self",
        through="RawConceptHierarchy",
        through_fields=("parent", "child"),
        symmetrical=False,
        related_name="parents",
    )
    terms = models.ManyToManyField(
        "RawTerm", through="RawConceptTermMapping", related_name="concepts"
    )


class RawConceptHierarchy(models.Model):
    parent = models.ForeignKey(
        "RawConcept", on_delete=models.CASCADE, related_name="child_links"
    )
    child = models.ForeignKey(
        "RawConcept", on_delete=models.CASCADE, related_name="parent_links"
    )
    list_order = models.CharField(max_length=2)


class RawTerm(models.Model):
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


class RawConceptTermMapping(models.Model):
    PREFERRED = "P"
    SYNONYM = "S"
    TERM_TYPE_CHOICES = [
        (PREFERRED, "Preferred"),
        (SYNONYM, "Synonym"),
    ]

    concept = models.ForeignKey("RawConcept", on_delete=models.CASCADE)
    term = models.ForeignKey("RawTerm", on_delete=models.CASCADE)
    term_type = models.CharField(max_length=1, choices=TERM_TYPE_CHOICES)


class TPPConcept(models.Model):
    read_code = models.CharField(primary_key=True, max_length=5)
    description = models.CharField(max_length=255)


class TPPRelationship(models.Model):
    ancestor = models.ForeignKey(
        "TPPConcept", on_delete=models.CASCADE, related_name="descendant_relationships"
    )
    descendant = models.ForeignKey(
        "TPPConcept", on_delete=models.CASCADE, related_name="ancestor_relationships"
    )
    distance = models.IntegerField()
