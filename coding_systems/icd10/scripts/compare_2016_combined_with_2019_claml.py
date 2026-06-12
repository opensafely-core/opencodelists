"""
Compare a merged ICD-10 2016 record set with WHO ICD-10 2019 ClaML.

The merged 2016 set is built from WHO 2016 ClaML and scraped NHS Class Browser
2016 ClaML using the decisions recorded in known_diffs.py.

Usage:

    python -m coding_systems.icd10.scripts.compare_2016_combined_with_2019_claml
"""

from coding_systems.icd10.release_builder import load_import_records


def main() -> None:
    try:
        load_import_records()
    except ValueError as e:
        print(str(e))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
