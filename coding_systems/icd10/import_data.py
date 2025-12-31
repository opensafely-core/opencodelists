import csv
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import structlog

from coding_systems.base.import_data_utils import CodingSystemImporter
from coding_systems.icd10.models import (
    Concept,
    ConceptEdition,
    ConceptKind,
    Edition,
    Rubric,
)


logger = structlog.get_logger()


def import_data(
    release_zipfile, release_name, valid_from, import_ref=None, check_compatibility=True
):
    with (
        TemporaryDirectory() as tempdir,
        CodingSystemImporter(
            "icd10", release_name, valid_from, import_ref, check_compatibility
        ) as database_alias,
    ):
        release_zip = ZipFile(release_zipfile)
        logger.info("Extracting", release_zip=release_zip.filename)

        release_zip.extractall(path=tempdir)
        path_2016 = Path(tempdir) / "flat.csv"
        assert path_2016.exists(), "Cannot stat combined 2016 file"
        paths_2019 = list(Path(tempdir).glob("icd102019syst_*.txt"))
        assert len(paths_2019) == 3, "All three 2019 files required"

        # ensure we start with an empty database
        assert not Concept.objects.using(database_alias).exists()

        with path_2016.open() as f:
            rows_2016 = list(csv.DictReader(f))

        records_rubrics_2016 = load_2016_concepts(rows_2016)
        created_concepts_2016 = Concept.objects.using(database_alias).bulk_create(
            Concept(**record) for record, _ in records_rubrics_2016
        )
        rubrics_2016 = [
            rr[0] | {"concept": concept}
            for rr, concept in zip(records_rubrics_2016, created_concepts_2016)
        ]
        Rubric.objects.using(database_alias).bulk_create(
            Rubric(**rubric) for rubric in rubrics_2016
        )

        ed_2016, _ = Edition.objects.using(database_alias).get_or_create(
            id="2016_combined",
            version=5,
            year=2016,
            source_description="Combined UK 2016 v5 edition from TRUD with scraped updated from NHS Browser. See bennettoxford/icd-browser-scraper for more info.",
        )

        ConceptEdition.objects.using(database_alias).bulk_create(
            ConceptEdition(concept=concept, edition=ed_2016)
            for concept in created_concepts_2016
        )

        ed_2019, _ = Edition.objects.using(database_alias).get_or_create(
            id="2019_who",
            version=6,
            year=2019,
            source_description="Downloaded from who.int website.",
        )

        with next(p for p in paths_2019 if p.name.endswith("chapters.txt")).open() as f:
            chapters_2019 = list(
                csv.DictReader(f, delimiter=";", fieldnames=["number", "term"])
            )
        chapters_2019 = [
            {
                "code": roman(int(chapter["number"])),
                "number": chapter["number"],
                "term": chapter["term"],
            }
            for chapter in chapters_2019
        ]

        ConceptEdition.objects.using(database_alias).bulk_create(
            ConceptEdition(
                concept_id=chapter["code"],
                edition=ed_2019,
                term=chapter["term"],
            )
            for chapter in chapters_2019
        )

        with next(p for p in paths_2019 if p.name.endswith("groups.txt")).open() as f:
            blocks_2019 = list(
                csv.DictReader(
                    f,
                    delimiter=";",
                    fieldnames=["start_code", "end_code", "chapter", "term"],
                )
            )
        blocks_2019 = [
            {
                "code": f"{block['start_code']}-{block['end_code']}",
                "kind": ConceptKind.BLOCK,
                "term": block["term"],
                "parent_id": next(
                    chapter
                    for chapter in chapters_2019
                    if chapter["number"] == block["chapter"]
                ),
            }
            for block in blocks_2019
        ]

        existing_blocks = {
            block["code"]
            for block in Concept.objects.using(database_alias)
            .filter(kind=ConceptKind.BLOCK)
            .values("code")
        }

        Concept.objects.using(database_alias).bulk_create(
            [
                Concept(**block)
                for block in blocks_2019
                if block["code"] not in existing_blocks
            ]
        )
        ConceptEdition.objects.using(database_alias).bulk_create(
            [
                ConceptEdition(
                    concept_id=block["code"],
                    edition=ed_2019,
                    term=block["term"] if block["code"] in existing_blocks else None,
                )
                for block in blocks_2019
            ]
        )

        with next(p for p in paths_2019 if p.name.endswith("codes.txt")).open() as f:
            categories_2019 = list(
                csv.DictReader(
                    f,
                    delimiter=";",
                    fieldnames=[
                        "level",
                        "terminal",
                        "terminal_type",
                        "chapter",
                        "parent",
                        "code_1",
                        "code_2",
                        "code",
                        "term",
                        "parent_term",
                        "term_2",
                        "n_0",
                        "n_1",
                        "n_2",
                        "n_3",
                        "n_4",
                    ],
                )
            )
        categories_2019 = [
            {
                k + "_id" if k == "parent" else k: v
                for k, v in category.items()
                if k in ["parent", "code", "term"]
            }
            | {"kind": ConceptKind.CATEGORY}
            for category in categories_2019
        ]

        for category in categories_2019:
            category["parent_id"] = next(
                block["code"]
                for block in blocks_2019
                if block["code"].startswith(category["parent_id"])
            )

        existing_categories = {
            category["code"]
            for category in Concept.objects.using(database_alias)
            .filter(kind=ConceptKind.CATEGORY)
            .values("code")
        }

        Concept.objects.using(database_alias).bulk_create(
            Concept(**category)
            for category in categories_2019
            if category["code"] not in existing_categories
        )

        ConceptEdition.objects.using(database_alias).bulk_create(
            [
                ConceptEdition(
                    edition=ed_2019,
                    concept_id=concept["code"],
                    term=""
                    if concept["code"] not in existing_categories
                    else concept["term"],
                )
                for concept in categories_2019
            ]
        )


def load_2016_concepts(rows):
    # "rubric_inclusion","modifier_4","rubric_text","kind","rubric_note","modifier_5","code","rubric_exclusion","parent","description"
    for row in rows:
        rubric = {
            k.replace("rubric_", ""): v
            for k, v in row.items()
            if k.startswith("rubric")
        }
        concept = (
            {
                k: v
                for k, v in row.items()
                if not k.startswith("rubric") and k not in ["description", "parent"]
            }
            | {
                "code": row["code"].replace(".", ""),
                "term": row["description"],
                "kind": ConceptKind(row["kind"]),
            }
            | ({"parent_id": row["parent"]} if row["parent"] else {})
        )
        yield (
            concept,
            rubric,
        )


def roman(integer):
    numbers = [1, 4, 5, 9, 10, 40, 50, 90, 100, 400, 500, 900, 1000]
    symbols = ["I", "IV", "V", "IX", "X", "XL", "L", "XC", "C", "CD", "D", "CM", "M"]
    i = len(numbers) - 1
    numerals = []
    while integer:
        div = integer // numbers[i]
        integer %= numbers[i]

        while div:
            numerals.append(symbols[i])
            div -= 1
        i -= 1

    return "".join(numerals)
