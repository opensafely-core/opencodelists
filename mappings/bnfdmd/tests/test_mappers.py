from codelists.coding_systems import CODING_SYSTEMS
from mappings.bnfdmd.mappers import bnf_to_dmd


def test_bnf_to_dmd(dmd_data, dmd_bnf_mapping_data):
    """Test mappers returns the correct format."""
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
