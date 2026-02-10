"""Import ICD-9 data from
https://ftp.cdc.gov/pub/health_statistics/nchs/publications/ICD-9/ucod.txt"""

import re
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import structlog

from coding_systems.base.import_data_utils import CodingSystemImporter
from coding_systems.icd9.models import Concept


logger = structlog.get_logger()

pat_chapter = re.compile(r"^\s+[IXV]{1,4}\..*")
pat_block = re.compile(r"^\s+[A-Z]{2,}[ A-Z]*\(\d+-\d+")
pat_category = re.compile(r"^\d{1,3}\.?\d?\s+.*$")


def import_data(
    release_zipfile,
    release_name,
    valid_from,
    import_ref=None,
    check_compatibility=False,
):
    with TemporaryDirectory() as tempdir:
        release_zip = ZipFile(release_zipfile)
        logger.info("Extracting", release_zip=release_zip.filename)

        release_zip.extractall(path=tempdir)
        # paths = list(Path(tempdir).glob("*CMS32_DESC_LONG_DX.txt"))
        # assert len(paths) == 1, (
        #     f"Expected 1 and only one CMS32_DESC_LONG_DX.txt file (found {len(paths)})"
        # )
        paths = list(Path(tempdir).glob("ucod.txt"))
        release_path = paths[0]

        with open(release_path, encoding="macroman") as f:
            lines = f.readlines()

    with CodingSystemImporter(
        "icd9", release_name, valid_from, import_ref, check_compatibility
    ) as database_alias:
        assert not Concept.objects.using(database_alias).exists()
        Concept.objects.using(database_alias).bulk_create(
            Concept(**record) for record in load_concepts(lines)
        )


def load_concepts(lines):
    last_chapter_id = ""
    last_block_id = ""
    last_category_id = ""
    for line in lines:
        if match := pat_chapter.match(line):
            parent_id = None
            kind = "chapter"
            code, term = (s.strip() for s in match.group().split("."))
            last_chapter_id = code
        elif match := pat_block.match(line):
            kind = "block"
            term, code = (s.strip() for s in match.group().split("("))
            last_block_id = code
            parent_id = last_chapter_id
        elif match := pat_category.match(line):
            kind = "category"
            matchstring = match.group()
            first_space = matchstring.find(" ")
            code = matchstring[:first_space]
            term = matchstring[first_space:].strip()
            if "." not in code:
                last_category_id = code
                parent_id = last_block_id
            else:
                parent_id = last_category_id
        else:
            continue
        yield {
            "code": code,
            "kind": kind,
            "term": term,
            "parent_id": parent_id,
        }
