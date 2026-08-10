import csv
from pathlib import Path

import structlog

from coding_systems.base.import_data_utils import CodingSystemImporter
from coding_systems.bnf.models import TYPES, Concept


logger = structlog.get_logger()


# Normalise ODP header names (for example, BNF_CHAPTER_CODE) so they match the
# BNF field names used by the importer.
def normalise(name: str) -> str:
    return name.upper().replace(" ", "_")


def import_data(
    release_csv, release_name, valid_from, import_ref=None, check_compatibility=True
):
    release_path = Path(release_csv)
    if release_path.suffix.lower() != ".csv":
        raise ValueError(f"Expected file path str ending '.csv', got '{release_path}'.")
    records = {type: set() for type in TYPES}
    with release_path.open(mode="r", newline="") as f:
        csv_reader = csv.DictReader(f)
        for r in csv_reader:
            parent_code = None
            for type in TYPES:
                name = r[normalise(f"BNF {type}")]
                code = r[normalise(f"BNF {type} Code")]
                if "DUMMY" not in name:
                    records[type].add((code, name, parent_code))
                    parent_code = code

    with CodingSystemImporter(
        "bnf", release_name, valid_from, import_ref, check_compatibility
    ) as database_alias:
        for type in TYPES:
            logger.info("Loading BNF type", type=type)
            for code, name, parent_code in sorted(records[type]):
                Concept.objects.using(database_alias).get_or_create(
                    code=code,
                    defaults={"name": name, "type": type, "parent_id": parent_code},
                )
