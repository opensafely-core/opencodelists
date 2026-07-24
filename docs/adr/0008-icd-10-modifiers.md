# ADR: Inclusion of complete set of modified codes in ICD-10

## Status

Accepted

## Context

ICD-10 uses a system of modifiers to allow concepts to further specified - e.g. an anatomical site where a disease is present, or the presence/non-presence of a common complication of a disease.
This is done by the appending of a fourth or fifth character to an existing ICD-10 code,
and a corresponding modification string to its term.
Modifier rules can be specified at multiple points in the hierarchical structure of ICD-10,
and inherited/overridden accordingly.

The previous implementation of the ICD-10 coding system did not fully capture all of the modifiers available.
Therefore, codelists created in this implementation of the ICD-10 coding system may be missing modified forms of certain ICD-10 codes.
This may not have been a serious problem around the time of this implementation,
because at that time clinical event data in OpenSAFELY was accessed via `cohort-extractor`,
which applied prefix matching rules to all ICD-10 codes.
`ehrQL` is now the only means of accessing clincial event data in OpenSAFELY,
and does not apply prefix matching to ICD-10 codes in all circumstances.

Therefore, when using `ehrQL`, and a codelist that is missing modified forms of ICD-10 codes,
clinical events may be missed.

## Decision

- All fourth and fifth character modifiers shall be applied to ICD-10 codes going forward
- Generation of modified codes shall be done at import time and they shall be treated as standard codes,
  - to reduce the need for model and frontend changes to support "native" modifier concepts
  - to eliminate user need to fully understand the ICD-10 modifier system
  - at the expense of some data repetition

## Consequences

- The ICD-10 ClaML parser now correctly extracts all modifiers
- The ICD-10 import process applies these modifiers to create new ICD-10 concepts with modified codes and terms
- Users can create codelists that are complete with respect to clinical event data in OpenSAFELY that is coded with modified ICD-10 codes

## Changes

- `coding_system/icd10/models.py` : add `term_modifier` and `modifier_position` attributes to `ConceptEdition`
- `coding_system/icd10/claml_parser.py` : fully support parsing of fourth and fifth character modifiers
- `coding_system/icd10/import_data.py` : populate modifier-related model fields from parsed ClaML
