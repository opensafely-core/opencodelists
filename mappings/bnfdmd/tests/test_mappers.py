from codelists.coding_systems import CODING_SYSTEMS
from coding_systems.bnf.models import Concept as BNFConcept
from mappings.bnfdmd.mappers import bnf_to_dmd
from mappings.bnfdmd.models import Mapping


def test_bnf_to_dmd(bnf_data, dmd_data):
    """Test mappers returns the correct format."""
    # create BNF Concepts
    BNFConcept.objects.using("bnf_test_20200101").get_or_create(
        code="0301012A0AA", type="Product", name="Adrenaline (Asthma)"
    )
    concept1, _ = BNFConcept.objects.using("bnf_test_20200101").get_or_create(
        code="0301012A0AAABAB",
        type="Presentation",
        name="Adrenaline (base) 220micrograms/dose inhaler",
    )
    concept2, _ = BNFConcept.objects.using("bnf_test_20200101").get_or_create(
        code="0301012A0AAACAC",
        type="Presentation",
        name="Adrenaline (base) 220micrograms/dose inhaler refill",
    )

    # Create the mappings for the 2 presentations; no mapping for the product
    Mapping.objects.create(
        dmd_code="10514511000001106",
        dmd_type="VMP",
        bnf_concept=concept1,
    )
    Mapping.objects.create(
        dmd_code="10525011000001107",
        dmd_type="VMP",
        bnf_concept=concept2,
    )

    mappings = bnf_to_dmd(
        ["0301012A0AA", "0301012A0AAABAB", "0301012A0AAACAC"],
        dmd_coding_system=CODING_SYSTEMS["dmd"].get_by_release_or_most_recent(),
    )
    expected = [
        {
            "dmd_type": "VMP",
            "dmd_id": "10514511000001106",
            "dmd_name": "Adrenaline (base) 220micrograms/dose inhaler",
            "bnf_code": "0301012A0AAABAB",
        },
        {
            "dmd_type": "VMP",
            "dmd_id": "10525011000001107",
            "dmd_name": "Adrenaline (base) 220micrograms/dose inhaler refill",
            "bnf_code": "0301012A0AAACAC",
        },
    ]
    assert mappings == expected
