import csv
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import structlog

from coding_systems.base.import_data_utils import CodingSystemImporter
from coding_systems.bnf.models import TYPES, Concept

logger = structlog.get_logger()


def import_data(
    release_zipfile, release_name, valid_from, import_ref=None, check_compatibility=True
):
    with TemporaryDirectory() as tempdir:
        release_zip = ZipFile(release_zipfile)
        logger.info("Extracting", release_zip=release_zip.filename)
        release_zip.extractall(path=tempdir)
        paths = list(Path(tempdir).glob("*.csv"))
        assert (
            len(paths) == 1
        ), f"Expected 1 and only one .csv file (found {len(paths)})"
        path = paths[0]

        records = {type: set() for type in TYPES}
        with open(path) as f:
            for r in csv.DictReader(f):
                parent_code = None
                for type in TYPES:
                    name = r[f"BNF {type}"]
                    code = r[f"BNF {type} Code"]
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
