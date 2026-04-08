"""Import ICD-9 data from
* https://www.cms.gov/medicare/coding/icd9providerdiagnosticcodes/downloads/icd-9-cm-v32-master-descriptions.zip
* https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Publications/ICD9-CM/2011/Dtab12.zip
  - (rtf converted to plaintext using striprtf https://pypi.org/project/striprtf/)

(Combine all above into a single zip file for loading)
"""

import re
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import structlog

from coding_systems.base.import_data_utils import CodingSystemImporter
from coding_systems.icd9.models import Concept


logger = structlog.get_logger()

pat_chapter = re.compile(r"\d{1,2}\.[ A-Z,\-]*\(\d+-\d+")
pat_block = re.compile(r"^[A-Z]{2,}[ A-Z,\-]*\(\d+-\d+")
pat_category = re.compile(r"^\d{3}\.?\d{0,2}\s+.*")
pat_block_rubrik = re.compile(r"^\d+-\d+ ")


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

        paths = list(Path(tempdir).glob("Dtab12.txt"))
        release_path = paths[0]

        with open(release_path) as f:
            cdc = f.readlines()

        cms = None
        paths = list(Path(tempdir).glob("*CMS32_DESC_LONG_DX.txt"))
        if paths:
            release_path = paths[0]
            with open(release_path, encoding="iso-8859-1") as f:
                cms = f.readlines()

    with CodingSystemImporter(
        "icd9", release_name, valid_from, import_ref, check_compatibility
    ) as database_alias:
        assert not Concept.objects.using(database_alias).exists()
        cdc_concepts = [Concept(**record) for record in load_cdc_concepts(cdc)]
        Concept.objects.using(database_alias).bulk_create(cdc_concepts)
        if cms:
            cms_concepts = [Concept(**record) for record in load_cms_concepts(cms)]
            # Couple of oddities which rubric says require "0" for 4th char
            # in lieu of explicit parent, so associate with grandparent
            all_codes = set(
                Concept.objects.using(database_alias)
                .all()
                .values_list("code", flat=True)
            ) | {c.code for c in cms_concepts}
            missing_cms_parent_codes = {
                c.parent_id for c in cms_concepts if c.parent_id not in all_codes
            }
            for concept in cms_concepts:
                if concept.parent_id in missing_cms_parent_codes:
                    concept.parent_id = concept.parent_id[
                        : len(concept.parent_id) - 1
                    ].rstrip(".")
            Concept.objects.using(database_alias).bulk_create(
                cms_concepts,
                # for now just update the singular record
                # we might want to add in as synonyms if term differs
                # we shouldn't expect parent_id or kind to change,
                # could probably do with something to catch that and blow up
                update_conflicts=True,
                update_fields=["term"],
                unique_fields=["code"],
            )


def load_cms_concepts(lines):
    for line in lines:
        code = line[:6].strip()
        code = code[:3] + "." + code[3:]
        try:
            float(code)
        except ValueError:
            continue
        term = line[6:].strip()
        parent_id = code[: len(code) - 1].rstrip(".")
        yield {
            "kind": "category",
            "code": code,
            "term": term,
            "parent_id": parent_id,
        }


def load_cdc_concepts(lines):
    last_chapter_id = ""
    last_block_id = ""
    last_category_id = ""
    last_line = ""
    for line in lines:
        if match := pat_chapter.match(line):
            parent_id = None
            kind = "chapter"
            code, term = match.group().split(" ", 1)
            code = code.rstrip(".")
            last_chapter_id = code
        elif match := pat_block.match(line):
            kind = "block"
            term, code = match.group().rsplit("(", 1)
            code = code
            last_block_id = code
            parent_id = last_chapter_id
        elif match := pat_category.match(line):
            if pat_block_rubrik.match(last_line):
                # we're in a block rubrik and have erroneously matched a category
                last_line = line
                continue
            kind = "category"
            code, term = match.group().split(" ", 1)
            if "." not in code:
                last_category_id = code
                parent_id = last_block_id
            else:
                parent_id = last_category_id
        else:
            last_line = line
            continue
        last_line = line
        yield {
            "code": code,
            "kind": kind,
            "term": term,
            "parent_id": parent_id,
        }
