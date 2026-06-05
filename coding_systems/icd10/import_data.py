import re

from django.db import transaction

from coding_systems.base.import_data_utils import (
    CodingSystemImporter,
    batched_bulk_create,
)
from coding_systems.icd10.claml_parser import parse_claml
from coding_systems.icd10.data_downloader import download_release
from coding_systems.icd10.models import (
    Concept,
    ConceptEdition,
    ConceptKind,
    ConceptUsage,
    DaggerAsteriskRelation,
    Edition,
)


def _normalise_code(code):
    return code.replace(".", "")


def _kind_for_code(code):
    # BLOCK if like A07-A09
    if re.match(r"^[A-Z]\d{2}-[A-Z]\d{2}$", code):
        return ConceptKind.BLOCK
    # CHAPTER is roman numeral
    if re.match(r"^[IVX]+$", code):
        return ConceptKind.CHAPTER
    # CATEGORY is A00, A00.0, A00.00, or A00.X0
    if re.match(r"^[A-Z]\d{2}(\.[X\d]\d?)?$", code):
        return ConceptKind.CATEGORY
    raise ValueError(f"Unrecognised ICD-10 code format: {code}")


def _normalise_parsed_output(parsed_output):
    normalised = {}
    for code, record in parsed_output.items():
        normalised_code = _normalise_code(code)
        normalised[normalised_code] = {
            "code": normalised_code,
            "kind": _kind_for_code(code),
            "description": record.description,
            "term_modifier": record.term_modifier,
            "modifier_position": record.modifier_position,
            "usage": record.usage,
            "usage_pair_codes": tuple(
                _normalise_code(related_code)
                for related_code in (record.usage_pair_codes or ())
            ),
            "parent": _normalise_code(record.parent) if record.parent else None,
        }
    return normalised


def _merged_code_records(normalised_output_2016, normalised_output_2019):
    normalised_outputs = [normalised_output_2016, normalised_output_2019]
    merged = {}
    all_codes = set(normalised_output_2016) | set(normalised_output_2019)

    for code in all_codes:
        records = [output[code] for output in normalised_outputs if code in output]
        parents = {record["parent"] for record in records}
        if len(parents) != 1:
            raise ValueError(
                f"Conflicting parent for ICD-10 code {code}: {sorted(parents)}"
            )
        merged[code] = records[-1]

    return merged


def _create_concepts(database_alias, merged_codes):
    batched_bulk_create(
        Concept,
        database_alias,
        (Concept(code=code) for code in merged_codes),
    )
    return {
        concept.code: concept for concept in Concept.objects.using(database_alias).all()
    }


def _set_concept_parents(database_alias, concepts_by_code, merged_codes):
    concepts_to_update = []

    for code, record in merged_codes.items():
        parent = record["parent"]
        if parent is None:
            continue
        if parent not in concepts_by_code:
            raise ValueError(f"Parent {parent} for ICD-10 code {code} was not imported")

        concepts_by_code[code].parent_id = parent
        concepts_to_update.append(concepts_by_code[code])

    Concept.objects.using(database_alias).bulk_update(concepts_to_update, ["parent"])


def _create_concept_editions(database_alias, concepts_by_code, edition_records):
    concept_editions = (
        ConceptEdition(
            concept=concepts_by_code[code],
            edition=edition,
            kind=record["kind"],
            usage=record["usage"] or ConceptUsage.NORMAL,
            term=record["description"],
            term_modifier=record["term_modifier"],
            modifier_position=record["modifier_position"],
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
                record["usage"]
                not in {
                    ConceptUsage.DAGGER,
                    ConceptUsage.ASTERISK,
                    "aster",  # TODO change the model so ConceptUsage.ASTERISK is actually "aster" and not "asterisk", and then remove this hack
                }
            ):
                continue

            for related_code in record["usage_pair_codes"]:
                related_key = (edition.id, related_code)
                if related_key not in concept_editions_by_key:
                    print(
                        f"DEBUG: Related code {related_code} for {code} in edition {edition.id} not found among imported concepts"
                    )
                    continue
                    # TODO what to do with related codes like "C91-C95" (i.e. not a code or a
                    # block, but a subset of a block), or B65- (assume this means any B65 code)
                    # raise ValueError(
                    #     f"ICD-10 usage reference {related_code} for {code} "
                    #     f"was not imported for edition {edition.id}"
                    # )

                dagger_code, asterisk_code = _relation_codes(
                    code, related_code, record["usage"]
                )
                relation_key = (edition.id, dagger_code, asterisk_code)
                if relation_key in seen_relations:
                    continue

                seen_relations.add(relation_key)
                relations.append(
                    DaggerAsteriskRelation(
                        dagger_concept=concept_editions_by_key[
                            (edition.id, dagger_code)
                        ],
                        asterisk_concept=concept_editions_by_key[
                            (edition.id, asterisk_code)
                        ],
                    )
                )

    batched_bulk_create(DaggerAsteriskRelation, database_alias, iter(relations))


def import_data(
    release_dir, release_name, valid_from, import_ref=None, check_compatibility=True
):
    xml_path_2016 = download_release(release_dir, "2016")
    xml_path_2019 = download_release(release_dir, "2019")
    output_2016 = parse_claml(xml_path_2016)
    output_2019 = parse_claml(xml_path_2019)
    normalised_output_2016 = _normalise_parsed_output(output_2016)
    normalised_output_2019 = _normalise_parsed_output(output_2019)

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
                    "WHO release of 2016 edition ICD-10, loaded from ClaML format from icd website."
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
            merged_codes = _merged_code_records(
                normalised_output_2016, normalised_output_2019
            )
            concepts_by_code = _create_concepts(database_alias, merged_codes)

            # Update the Concept records with the FK parent relation
            _set_concept_parents(database_alias, concepts_by_code, merged_codes)

            # We have the Editions and Concepts, so now add the ConceptEdition records
            edition_records = [
                (edition_2016, normalised_output_2016),
                (edition_2019, normalised_output_2019),
            ]
            concept_editions_by_key = _create_concept_editions(
                database_alias, concepts_by_code, edition_records
            )

            # Next we can create the DaggerAsteriskRelation records, which require the ConceptEdition records to already exist
            _create_dagger_asterisk_relations(
                database_alias, edition_records, concept_editions_by_key
            )

            # TODO Finally we add the ConceptRubrics and the ModifierRubrics
