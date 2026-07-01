"""
Compare WHO ICD-10 2016 ClaML with scraped NHS Class Browser 2016 ClaML.

Reports codes present in only one source and codes whose descriptions (terms) differ.

Usage:

    python -m coding_systems.icd10.scripts.compare_2016_claml_with_scraped
"""

import structlog

from coding_systems.icd10.release_builder import combine_2016_claml_and_scraped_records


logger = structlog.get_logger()


def main() -> None:
    try:
        combine_2016_claml_and_scraped_records()
    except ValueError as e:
        logger.error(str(e))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
