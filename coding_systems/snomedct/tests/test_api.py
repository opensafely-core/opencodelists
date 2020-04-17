from django.test import TestCase


class TestAPI(TestCase):
    fixtures = ["snomedct"]

    # * SNOMED CT Concept (SNOMED RT+CTV3)
    #   * Characteristic type (core metadata concept)
    #     * Additional relationship (core metadata concept)
    #     * Defining relationship (core metadata concept)
    #       * Inferred relationship (core metadata concept)
    #       * Stated relationship (core metadata concept)
    #     * Qualifying relationship (core metadata concept)
    #   * ...

    def test_concepts_grandparent(self):
        # fmt: off
        expected_concepts = [
            {
                "id": "900000000000449001",
                "fully_specified_name": "Characteristic type (core metadata concept)",
                "child_ids": [
                    "900000000000227009",  # >------------------------------------------------+
                    "900000000000006009",  # >--------------------------------------------------+
                    "900000000000225001",  # >----------------------------------------------------+
                ],                                                                          # | | |
                "fetched_all_children": True,                                               # | | |
            },                                                                              # | | |
            {                                                                               # | | |
                "id": "900000000000227009",  # <----------------------------------------------+ | |
                "fully_specified_name": "Additional relationship (core metadata concept)",    # | |
                "child_ids": [],                                                              # | |
                "fetched_all_children": True,                                                 # | |
            },                                                                                # | |
            {                                                                                 # | |
                "id": "900000000000006009",  # <------------------------------------------------+ |
                "fully_specified_name": "Defining relationship (core metadata concept)",        # |
                "child_ids": [                                                                  # |
                    "900000000000011006",  # >------------------------------------------------+   |
                    "900000000000010007",  # >--------------------------------------------------+ |
                ],                                                                          # | | |
                "fetched_all_children": True,                                               # | | |
            },                                                                              # | | |
            {                                                                               # | | |
                "id": "900000000000011006",  # <----------------------------------------------+ | |
                "fully_specified_name": "Inferred relationship (core metadata concept)",      # | |
                "child_ids": [],                                                              # | |
                "fetched_all_children": False,                                                # | |
            },                                                                                # | |
            {                                                                                 # | |
                "id": "900000000000010007",  # <------------------------------------------------+ |
                "fully_specified_name": "Stated relationship (core metadata concept)",          # |
                "child_ids": [],                                                                # |
                "fetched_all_children": False,                                                  # |
            },                                                                                  # |
            {                                                                                   # |
                "id": "900000000000225001",  # <--------------------------------------------------+
                "fully_specified_name": "Qualifying relationship (core metadata concept)",
                "child_ids": [],
                "fetched_all_children": True,
            },
        ]
        # fmt: on

        self.assertConcepts(expected_concepts, ["900000000000449001"])

    def test_concepts_grandparent_with_ancestors(self):
        # fmt: off
        expected_concepts = [
            {
                "id": "138875005",
                "fully_specified_name": "SNOMED CT Concept (SNOMED RT+CTV3)",
                "child_ids": [
                    "900000000000441003"  # >-----+
                ],                              # |
                "fetched_all_children": False,  # |
            },                                  # |
            {                                   # |
                "id": "900000000000441003",  # <--+
                "fully_specified_name": "SNOMED CT Model Component (metadata)",
                "child_ids": [
                    "900000000000442005"  # >-----+
                ],                              # |
                "fetched_all_children": False,  # |
            },                                  # |
            {                                   # |
                "id": "900000000000442005",  # <--+
                "fully_specified_name": "Core metadata concept (core metadata concept)",
                "child_ids": [
                    "900000000000449001"  # >-----+
                ],                              # |
                "fetched_all_children": False,  # |
            },                                  # |
            {                                   # |
                "id": "900000000000449001",  # <--+
                "fully_specified_name": "Characteristic type (core metadata concept)",
                "child_ids": [
                    "900000000000227009",  # >------------------------------------------------+
                    "900000000000006009",  # >--------------------------------------------------+
                    "900000000000225001",  # >----------------------------------------------------+
                ],                                                                          # | | |
                "fetched_all_children": True,                                               # | | |
            },                                                                              # | | |
            {                                                                               # | | |
                "id": "900000000000227009",  # <----------------------------------------------+ | |
                "fully_specified_name": "Additional relationship (core metadata concept)",    # | |
                "child_ids": [],                                                              # | |
                "fetched_all_children": True,                                                 # | |
            },                                                                                # | |
            {                                                                                 # | |
                "id": "900000000000006009",  # <------------------------------------------------+ |
                "fully_specified_name": "Defining relationship (core metadata concept)",        # |
                "child_ids": [                                                                  # |
                    "900000000000011006",  # >------------------------------------------------+   |
                    "900000000000010007",  # >--------------------------------------------------+ |
                ],                                                                          # | | |
                "fetched_all_children": True,                                               # | | |
            },                                                                              # | | |
            {                                                                               # | | |
                "id": "900000000000011006",  # <----------------------------------------------+ | |
                "fully_specified_name": "Inferred relationship (core metadata concept)",      # | |
                "child_ids": [],                                                              # | |
                "fetched_all_children": False,                                                # | |
            },                                                                                # | |
            {                                                                                 # | |
                "id": "900000000000010007",  # <------------------------------------------------+ |
                "fully_specified_name": "Stated relationship (core metadata concept)",          # |
                "child_ids": [],                                                                # |
                "fetched_all_children": False,                                                  # |
            },                                                                                  # |
            {                                                                                   # |
                "id": "900000000000225001",  # <--------------------------------------------------+
                "fully_specified_name": "Qualifying relationship (core metadata concept)",
                "child_ids": [],
                "fetched_all_children": True,
            },
        ]
        # fmt: on

        self.assertConcepts(expected_concepts, ["900000000000449001"], include_ancestors=True)

    def test_concepts_parent(self):
        # fmt: off
        expected_concepts = [
            {
                "id": "900000000000006009",
                "fully_specified_name": "Defining relationship (core metadata concept)",
                "child_ids": [
                    "900000000000011006",
                    "900000000000010007",
                ],
                "fetched_all_children": True,
            },
            {
                "id": "900000000000011006",
                "fully_specified_name": "Inferred relationship (core metadata concept)",
                "child_ids": [],
                "fetched_all_children": True,
            },
            {
                "id": "900000000000010007",
                "fully_specified_name": "Stated relationship (core metadata concept)",
                "child_ids": [],
                "fetched_all_children": True,
            },
        ]
        # fmt: on

        self.assertConcepts(expected_concepts, ["900000000000006009"])

    def test_concepts_leaf(self):
        # fmt: off
        expected_concepts = [
            {
                "id": "900000000000011006",
                "fully_specified_name": "Inferred relationship (core metadata concept)",
                "child_ids": [],
                "fetched_all_children": True,
            },
        ]
        # fmt: on

        self.assertConcepts(expected_concepts, ["900000000000011006"])

    def assertConcepts(self, expected_concepts, ids, include_ancestors=False):
        url = f"/api/v1/snomedct/concepts/?concepts={','.join(ids)}"
        if include_ancestors:
            url += "&include_ancestors=true"

        rsp = self.client.get(url)
        concepts = {c["id"]: c for c in rsp.json()["concepts"]}
        expected_concepts = {c["id"]: c for c in expected_concepts}

        self.assertEqual(concepts.keys(), expected_concepts.keys())

        for id in concepts:
            concept = concepts[id]
            expected = expected_concepts[id]

            self.assertEqual(
                concept["fully_specified_name"], expected["fully_specified_name"], id
            )
            self.assertEqual(concept["child_ids"], expected["child_ids"], id)
