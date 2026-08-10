import csv
from pathlib import Path

import structlog

from coding_systems.base.import_data_utils import CodingSystemImporter
from coding_systems.bnf.models import TYPES, Concept


logger = structlog.get_logger()


def import_data(
    release_csv, release_name, valid_from, import_ref=None, check_compatibility=True
):
    release_path = Path(release_csv)
    if release_path.suffix.lower() != ".csv":
        raise ValueError(f"Expected file path str ending '.csv', got '{release_path}'.")
    records = {concept_type: set() for concept_type in TYPES}
    with release_path.open(mode="r", newline="") as f:
        csv_reader = csv.DictReader(f)
        for row in csv_reader:
            parent_code = None
            for concept_type in TYPES:
                concept_type_column_header = concept_type.upper().replace(" ", "_")
                name = row[f"BNF_{concept_type_column_header}"]
                code = row[f"BNF_{concept_type_column_header}_CODE"]

                records[concept_type].add((code, name, parent_code))
                parent_code = code

    with CodingSystemImporter(
        "bnf", release_name, valid_from, import_ref, check_compatibility
    ) as database_alias:
        for concept_type in TYPES:
            logger.info("Loading BNF type", type=concept_type)
            for code, name, parent_code in sorted(records[concept_type]):
                Concept.objects.using(database_alias).get_or_create(
                    code=code,
                    defaults={
                        "name": name,
                        "type": concept_type,
                        "parent_id": parent_code,
                    },
                )
