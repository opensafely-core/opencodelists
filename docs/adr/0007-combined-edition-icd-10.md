# ADR: Combining Multiple ICD-10 Editions into a single Coding System

Date: 2026-07

## Status

Accepted

## Context

The International Classification of Diseases, 10th Revision (ICD-10) coding system is published by the World Health Organisation.
They have published 6 editions: 2008, 2010, 2015, 2016, 2019, 2019+COVID-19.
These editions are available in a plain-text format and an XML format called ClaML.
The pre-existing ICD-10 releases in OpenCodelists were loaded by downloading and parsing ClaML files.

The NHS publishes a variant of the WHO 2016 edition, solely available as a web-based coding system browser.
Many efforts were made to obtain this edition in a structured format but we were repeatedly told that such a thing does not exist.

There are currently two datasources available in OpenSAFELY-TPP that use ICD-10 coded data:
- Admitted Patient Care Spells (APCS)
- Registered Deaths (ONS Deaths)

The former uses the 2016 edition of ICD-10 with some NHS-specific modifications.
The latter uses the 2019 edition (with some apparent very minor ONS-specific modifications which appear to mirror some of the NHS modifications, based on analysis of the codes present in the ONS Deaths data).

There are differences between these editions:
- some concepts are present in one edition and not the other
- some concepts are present in both editions, but use different codes
- some concepts are present in both editions with the same code but have minor differences in their descriptions
- some concepts are present in both editions, but with potentially clinically or epidemiologically significant differences in their descriptions

Before this change, the only edition of ICD-10 available in OpenCodelists was the WHO-provided 2019+COVID-19 edition.
Use of codelists created with this edition with the APCS dataset may result in missed clinical events due to the differences between these editions.

## Decision

- We will provide data from both the 2016 (NHS modified) and 2019+Covid-19 Editions of ICD-10,
such that codelists can be created that are useable in both APCS and ONS Deaths datasets.
- We will combine data from both these editions into a single coding system,
to reduce user confusion as to which edition they should use for which dataset.
- We will use the existing ICD-10 coding system for this new combined data,
to avoid having to migrate existing codelists to a new system,
and reduce user confusion about multiple ICD-10 coding systems,
and reduce risk of old codelists in a defunct coding system with known errors introducing errors into studies
- We will notify users where existing codelists may have missing codes due to the differences between these editions
- We will notify users where existing codelists contain codes that have significant definitional differences between these editions

## Consequences

- The ICD-10 Coding System model allows for storage of multiple editions within a single Release
  - Properties of an ICD-10 concept that may vary by edition are stored at the level of a mapping between a concept and an edition
  - Single-edition previous releases' data are migrated to this new structure
  - The ICD-10 coding system interface methods are updated to access data from this multi-edition structure, and contain business rules to prioritise data from one edition over another as necessary
- The ICD-10 Coding System import process downloads and imports the necessary data from the NHS and WHO for these two editions
  - The 2016 and 2019 editions will be downloaded from the WHO website in ClaML format
  - The NHS ICD-10 coding system browser will be scraped and the scraped data translated to ClaML format
  - Due to the inherent risks of scraping, the WHO and NHS 2016 editions will be combined in such a way to ensure as complete a 2016-NHS edition as possible
  - Significant/insignificant differences between editions are defined a priori, and any new differences are assumed potentially significant and requiring of human review. The import process will halt upon discovery of such differences to prompt such a review.
  - As per other coding systems, a new release will be not be imported if there are no differences between it and a previous release

## Changes

- `coding_systems/icd10/models.py` : Changed to add multi-edition supporting structures
- `coding_systems/icd10/coding_system.py` : Coding system interface methods updated to support multi-edition model, added edition prioritisation logic where needed
- `coding_systems/icd10/claml_parser.py` : A more complete ClaML parser added to support these new editions
- `coding_systems/icd10/data_downloader.py` : Downloads all required editions and combine them into a single zip file for loading
- `coding_systems/icd10/import_data.py` : Modified to load combined zip file of editions, executes difference checking, load into new model
- `coding_systems/icd10/known_diffs.py` : Listings of known differences between editions and supporting logic
- `coding_systems/icd10/release_builder.py` : Contains edition combination logic and difference checking/reporting functions, provides finalised editions ready for import
- `coding_systems/icd10/scrape.py` : NHS ICD-10 browser scraper
- `coding_systems/icd10/scraped_to_claml.py` : Converts scraped NHS ICD-10 data into ClaML format
- builder and codelistversion views: Added warning banners to be shown when codes with known significant issues present
