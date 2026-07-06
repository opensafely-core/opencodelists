import re

from django.db import transaction

from coding_systems.base.import_data_utils import (
    CodingSystemImporter,
    batched_bulk_create,
)
from coding_systems.icd10.claml_parser import ICD10Code
from coding_systems.icd10.data_downloader import Downloader
from coding_systems.icd10.models import (
    Concept,
    ConceptEdition,
    ConceptKind,
    ConceptRubric,
    ConceptUsage,
    DaggerAsteriskRelation,
    Edition,
    ModifierRubric,
)
from coding_systems.icd10.release_builder import load_import_records


def _kind_for_code(code):
    """Determine the kind of an ICD-10 code based on its format"""
    # BLOCK if like A07-A09
    if re.match(r"^[A-Z]\d{2}-[A-Z]\d{2}$", code):
        return ConceptKind.BLOCK
    # CHAPTER is Roman numeral
    if re.match(r"^[IVX]+$", code):
        return ConceptKind.CHAPTER
    # CATEGORY is A00, A000, A0000, or A00X0
    if re.match(r"^[A-Z]\d{2}([X\d]\d?)?$", code):
        return ConceptKind.CATEGORY
    raise ValueError(f"Unrecognised ICD-10 code format: {code}")


def _merge_code_parent_relationships(
    output_2016: dict[str, ICD10Code], output_2019: dict[str, ICD10Code]
) -> dict[str, str]:
    """Merge the child/parent relationships from the 2016 and 2019 editions, checking for any conflicts."""
    outputs = [output_2016, output_2019]
    merged = {}
    all_codes = set(output_2016) | set(output_2019)

    for code in all_codes:
        parents = {output[code].parent for output in outputs if code in output}
        if len(parents) != 1:
            raise ValueError(
                f"Conflicting parent for ICD-10 code {code}: {sorted(parents)}"
            )
        merged[code] = parents.pop()

    return merged


def _create_concepts(database_alias, codes):
    batched_bulk_create(
        Concept,
        database_alias,
        (Concept(code=code) for code in codes),
    )
    return {
        concept.code: concept for concept in Concept.objects.using(database_alias).all()
    }


def _set_concept_parents(
    database_alias,
    concepts_by_code: dict[str, Concept],
    child_parent_map: dict[str, str],
):
    concepts_to_update = []

    for child, parent in child_parent_map.items():
        if parent is None:
            continue
        if parent not in concepts_by_code:
            raise ValueError(
                f"Parent {parent} for ICD-10 code {child} was not imported"
            )

        concepts_by_code[child].parent_id = parent
        concepts_to_update.append(concepts_by_code[child])

    Concept.objects.using(database_alias).bulk_update(concepts_to_update, ["parent"])


def _create_concept_editions(
    database_alias,
    concepts_by_code: dict[str, Concept],
    edition_records: list[tuple[Edition, dict[str, ICD10Code]]],
):
    concept_editions = (
        ConceptEdition(
            concept=concepts_by_code[code],
            edition=edition,
            kind=_kind_for_code(code),
            usage=record.usage or ConceptUsage.NORMAL,
            term=record.term,
            term_modifier=record.term_modifier,
            modifier_position=record.modifier_position,
        )
        for edition, records in edition_records
        for code, record in records.items()
    )
    batched_bulk_create(ConceptEdition, database_alias, concept_editions)

    return {
        (concept_edition.edition_id, concept_edition.concept.code): concept_edition
        for concept_edition in ConceptEdition.objects.using(
            database_alias
        ).select_related("concept")
    }


def _relation_codes(code, related_code, usage):
    if usage == ConceptUsage.DAGGER:
        return code, related_code
    return related_code, code


def _create_dagger_asterisk_relations(
    database_alias, edition_records, concept_editions_by_key
):
    relations = []
    seen_relations = set()

    for edition, records in edition_records:
        for code, record in records.items():
            if (
                record.usage
                not in {
                    ConceptUsage.DAGGER,
                    ConceptUsage.ASTERISK,
                    "aster",  # TODO change the model so ConceptUsage.ASTERISK is actually "aster" and not "asterisk", and then remove this hack
                }
            ):
                continue

            for related_code in record.usage_pair_codes or ():
                dagger_code, asterisk_code = _relation_codes(
                    code, related_code, record.usage
                )
                relation_key = (edition.id, dagger_code, asterisk_code)
                if relation_key in seen_relations:
                    continue

                seen_relations.add(relation_key)
                relations.append(
                    DaggerAsteriskRelation(
                        dagger_code=dagger_code,
                        dagger_concept=concept_editions_by_key.get(
                            (edition.id, dagger_code)
                        ),
                        asterisk_code=asterisk_code,
                        asterisk_concept=concept_editions_by_key.get(
                            (edition.id, asterisk_code)
                        ),
                    )
                )

    batched_bulk_create(DaggerAsteriskRelation, database_alias, iter(relations))


def _add_rubrics(database_alias, edition_records, concept_editions_by_key):
    concept_rubrics_to_create = []
    modifier_rubrics_to_create = []
    for edition, records in edition_records:
        for code, record in records.items():
            if not record.concept_rubrics and not record.modifier_rubrics:
                continue
            key = (edition.id, code)
            assert key in concept_editions_by_key

            for kind, rubric_list in record.concept_rubrics.items():
                for rubric in rubric_list:
                    concept_rubrics_to_create.append(
                        ConceptRubric(
                            concept_edition=concept_editions_by_key[key],
                            text=rubric,
                            kind=kind,
                        )
                    )
            for kind, rubric_list in record.modifier_rubrics.items():
                for rubric in rubric_list:
                    modifier_rubrics_to_create.append(
                        ModifierRubric(
                            concept_edition=concept_editions_by_key[key],
                            text=rubric,
                            kind=kind,
                        )
                    )

    batched_bulk_create(
        ConceptRubric,
        database_alias,
        iter(concept_rubrics_to_create),
    )
    batched_bulk_create(
        ModifierRubric,
        database_alias,
        iter(modifier_rubrics_to_create),
    )


def import_data(
    release_dir, release_name, valid_from, import_ref=None, check_compatibility=True
):
    downloader = Downloader(release_dir)
    release_zipfile_path, metadata = downloader.download_latest_release()
    import_release(
        release_zipfile_path,
        import_ref,
        check_compatibility,
        release_name=release_name,
        valid_from=valid_from,
        **metadata,
    )


def import_release(
    release_zipfile,
    import_ref=None,
    check_compatibility=True,
    release_name=None,
    valid_from=None,
    file_metadata=None,
    **kwargs,
):
    import_ref = import_ref or release_zipfile.name
    output_2016, output_2019 = load_import_records(release_zipfile, file_metadata)
    with CodingSystemImporter(
        "icd10", release_name, valid_from, import_ref, check_compatibility
    ) as database_alias:
        with transaction.atomic(using=database_alias):
            # First we create the two editions
            edition_2016 = Edition.objects.using(database_alias).create(
                id="2016",
                version=20160101,
                year=2016,
                source_description=(
                    "Combined 2016 ICD-10 edition, loaded from WHO ClaML and "
                    "scraped NHS Class Browser ClaML."
                ),
            )
            edition_2019 = Edition.objects.using(database_alias).create(
                id="2019",
                version=20190101,
                year=2019,
                source_description=(
                    "WHO release of 2019 edition ICD-10, loaded from ClaML format from icd website."
                ),
            )

            # Create the Concept records from the merged 2016 and 2019 codes
            all_codes = set(output_2016) | set(output_2019)
            concepts_by_code = _create_concepts(database_alias, all_codes)

            # Update the Concept records with the FK parent relation
            child_parent_map = _merge_code_parent_relationships(
                output_2016, output_2019
            )
            _set_concept_parents(database_alias, concepts_by_code, child_parent_map)

            # We have the Editions and Concepts, so now add the ConceptEdition records
            edition_records = [
                (edition_2016, output_2016),
                (edition_2019, output_2019),
            ]
            concept_editions_by_key = _create_concept_editions(
                database_alias, concepts_by_code, edition_records
            )

            # Next we can create the DaggerAsteriskRelation records, which require the ConceptEdition records to already exist
            _create_dagger_asterisk_relations(
                database_alias, edition_records, concept_editions_by_key
            )

            # Finally we add the ConceptRubrics and the ModifierRubrics
            _add_rubrics(database_alias, edition_records, concept_editions_by_key)
