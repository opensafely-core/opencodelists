"""Import ICD-10 data from
https://apps.who.int/classifications/apps/icd/ClassificationDownload/DLArea/Download.aspx"""

import pickle
from collections import defaultdict
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import structlog
from lxml import etree

from coding_systems.base.import_data_utils import CodingSystemImporter
from coding_systems.icd10.models import Concept


logger = structlog.get_logger()


def import_data(
    release_zipfile, release_name, valid_from, import_ref=None, check_compatibility=True
):
    doc = extract_document(release_zipfile)

    with CodingSystemImporter(
        "icd10", release_name, valid_from, import_ref, check_compatibility
    ) as database_alias:
        # ensure we start with an empty database
        assert not Concept.objects.using(database_alias).exists()
        Concept.objects.using(database_alias).bulk_create(
            Concept(**record) for record in load_concepts(doc)
        )


def extract_document(release_zipfile):
    with TemporaryDirectory() as tempdir:
        release_zip = ZipFile(release_zipfile)
        logger.info("Extracting", release_zip=release_zip.filename)

        release_zip.extractall(path=tempdir)
        paths = list(Path(tempdir).glob("*.xml")) or list(
            Path(tempdir).glob("*.pickle")
        )
        assert len(paths) == 1, (
            f"Expected 1 and only one .xml or .pickle file (found {len(paths)})"
        )
        release_path = paths[0]

        if release_path.suffix == ".xml":
            with open(release_path) as f:
                doc = etree.parse(f)
        else:
            with release_path.open("rb") as f:
                doc = pickle.load(f)

    return doc


def load_concepts(doc):
    """
    If "doc" is actually a combined pre-processed release Concept set,
    yield dict of Concept attributes from it.

    Otherwise, yield dicts with `code`, `kind`, `term` and `parent_id` attributes of all
    concepts.

    Concepts are defined in `Class` elements, which have `code` and `kind` attributes.
    They have one or more `Rubric` elements as children, and we choose one of them for
    the term.  Additionally, non-chapter `Class` elements have a single `SuperClass`
    child, which contains the `parent_id`.

    Several `Class` elements also have a `ModifiedBy` child, which references a number
    of `ModifierClass` elements.  For instance, we have:

    <ClaML version="2.0.0">
        <Class code="E13" kind="category">
            <SuperClass code="E10-E14"/>
            <ModifiedBy code="S04E10_4"/>
            <Rubric kind="preferred">
                <Label>Other specified diabetes mellitus</Label>
            </Rubric>
        </Class>
        ...
        <ModifierClass code=".0" modifier="S04E10_4">
            <SuperClass code="S04E10_4"/>
            <Rubric kind="preferred">
                    <Label>With coma</Label>
            </Rubric>
        </ModifierClass>
        <ModifierClass code=".1" modifier="S04E10_4">
            <SuperClass code="S04E10_4"/>
            <Rubric kind="preferred">
                <Label>With ketoacidosis</Label>
            </Rubric>
        </ModifierClass>
        ...
    </ClaML>

    This means that category E13 has descendants E13.0 and E13.1, which we label as
    "Other specified diabetes mellitus : With coma" and "Other specified diabetes
    mellitus : With ketoacidosis".

    Note that in order to match the format the ICD-10 codes are recorded in SUS and
    elsewhere, we strip the `.` from codes.  So eg `E13.0` is recorded as `E130`.  We
    don't think that this ever introduces ambiguity!
    """

    if isinstance(doc, set):
        for concept in doc:
            yield {k: v for k, v in concept.__dict__.items() if not k.startswith("_")}

    root = doc.getroot()

    modifiers = defaultdict(list)

    def get_label(el):
        label = e.find("Rubric[@kind='preferredLong']/Label")
        if label is None:
            label = e.find("Rubric[@kind='preferred']/Label")
        return label

    for e in root.findall("ModifierClass"):
        modifier = e.get("modifier")
        code = e.get("code")
        if code[0] != ".":
            continue

        label = get_label(e)
        term = " ".join(label.itertext())

        modifiers[modifier].append((code[1:], term))

    for e in root.findall("Class"):
        code = e.get("code")
        kind = e.get("kind")

        if kind == "category":
            if len(code) == 5:
                assert code[3] == "."
                code = code.replace(".", "")

        label = get_label(e)
        term = " ".join(label.itertext())

        superclass = e.find("SuperClass")
        if superclass is not None:
            parent_id = superclass.get("code")
        else:
            parent_id = None

        yield {
            "code": code,
            "kind": kind,
            "term": term,
            "parent_id": parent_id,
        }

        for modified_by in e.findall("ModifiedBy"):
            modifier_code = modified_by.get("code")
            modifier = modifiers[modifier_code]
            if not modifier:
                continue

            assert kind == "category"

            for modifier_code, modifier_term in modifier:
                yield {
                    "code": code + modifier_code,
                    "kind": kind,
                    "term": term + " : " + modifier_term,
                    "parent_id": code,
                }
