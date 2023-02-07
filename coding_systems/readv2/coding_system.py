from ..base.coding_system_base import DummyCodingSystem


class CodingSystem(DummyCodingSystem):
    id = "readv2"
    name = "Read V2"
    short_name = "Read V2"
    csv_headers = {
        "code": ["code", "readcode"],
        "term": ["term", "readcodedescr"],
        "category": ["category"],
    }
