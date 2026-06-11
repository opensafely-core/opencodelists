"""
Refresh the WHO ICD-10 ClaML ZIP metadata record. Used to discover when the
source XML files have been updated, which tells us that we need to create a
new combined release of ICD10.

Usage:

    python -m coding_systems.icd10.scripts.check_icd10_claml_zip_timestamps
"""

from coding_systems.icd10.release_metadata import check_claml_zip_metadata


def main() -> None:
    check_claml_zip_metadata()


if __name__ == "__main__":
    main()
