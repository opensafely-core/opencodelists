import json
from pathlib import Path

from .models import AffectedCodelist


def load_example_codelists() -> list[AffectedCodelist]:
    """Load the fixed example data captured from the database snapshot."""
    fixture_path = Path(__file__).parent / "icd10_report_example.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    return [
        AffectedCodelist(
            name=item["name"],
            slug=item["slug"],
            user_id=item["user_id"],
            organisation_id=item["organisation_id"],
            version_id=item["version_id"],
            version_tag=item["version_tag"],
            codes=frozenset(item["codes"]),
            description_changes=item["description_changes"],
            moved_code_sets=item["moved_code_sets"],
        )
        for item in fixture["codelists"]
    ]
