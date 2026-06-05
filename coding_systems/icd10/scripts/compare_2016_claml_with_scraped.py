"""
Compare WHO ICD-10 2016 ClaML with scraped NHS Class Browser 2016 ClaML.

Reports codes present in only one source and codes whose descriptions (terms) differ.

Usage:

    python -m coding_systems.icd10.scripts.compare_2016_claml_with_scraped
"""

from pathlib import Path

from coding_systems.icd10.claml_parser import (
    ICD10Code,
    parse_claml,
)
from coding_systems.icd10.data_downloader import download_release
from coding_systems.icd10.known_diffs import (
    apply_nhs_2016_alterations,
    is_2016_claml_only,
    is_2016_description_difference,
    is_2016_scraped_only,
)


ICD10_ROOT = Path(__file__).parent.parent
RELEASE_DIR = ICD10_ROOT / "data"
SCRAPED_CLAML = RELEASE_DIR / "scraped_classbrowser_2016.xml"
BANNER_WIDTH = 79


def _description_with_modifier(record: ICD10Code) -> str:
    if record.term_modifier:
        return f"{record.description} ({record.term_modifier})"
    return record.description


def diff_records(
    claml_records: dict[str, ICD10Code],
    scraped_records: dict[str, ICD10Code],
    print_output: bool = False,
) -> bool:
    claml_codes = set(claml_records)
    scraped_codes = set(scraped_records)

    claml_only_codes = sorted(claml_codes - scraped_codes)
    # We only care about CLAML-only codes that are not already known via the known_diffs.py file
    unknown_claml_only_codes = [
        code for code in claml_only_codes if not is_2016_claml_only(code)
    ]

    scraped_only_codes = sorted(scraped_codes - claml_codes)
    # We only care about scraped-only codes that are not already known via the known_diffs.py file
    unknown_scraped_only_codes = [
        code for code in scraped_only_codes if not is_2016_scraped_only(code)
    ]

    description_difference_count = 0
    unknown_term_differences = []
    for code in sorted(claml_codes & scraped_codes):
        claml_description = _description_with_modifier(claml_records[code])
        scraped_description = _description_with_modifier(scraped_records[code])
        if claml_description == scraped_description:
            continue

        description_difference_count += 1
        if not is_2016_description_difference(
            code,
            claml_description,
            scraped_description,
        ):
            # We only care about description differences that are not already known via the known_diffs.py file
            unknown_term_differences.append(
                (code, claml_description, scraped_description)
            )

    if print_output:
        print(
            "\n\nCompared WHO 2016 ClaML with scraped NHS Class Browser 2016 ClaML\n\n"
            f"CLAML records:   {len(claml_records)}\n"
            f"Scraped records: {len(scraped_records)}\n\n"
            "Summary\n-------\n"
            f"CLAML-only codes:  {len(claml_only_codes)} (of which {len(unknown_claml_only_codes)} unknown)\n"
            f"Scraped-only codes:  {len(scraped_only_codes)} (of which {len(unknown_scraped_only_codes)} unknown)\n"
            f"Description changes:  {description_difference_count} (of which {len(unknown_term_differences)} unknown)"
        )

    has_unknown_diffs = any(
        (
            unknown_claml_only_codes,
            unknown_scraped_only_codes,
            unknown_term_differences,
        )
    )

    if not has_unknown_diffs:
        if print_output:
            print("\n✅ ALL OK: every difference is expected\n")
        return True

    if print_output:
        if unknown_claml_only_codes:
            print(
                "\nCLAML-only codes\n----------------\n"
                "There are codes in the CLAML, but not in the scraped. This could be:\n"
                " - A code that was added to the CLAML but not the scraped\n"
                " - A code has been removed from the scraped but not the CLAML\n\n"
                "Once you've decided whether you want to include or exclude each one below,\n"
                "add the following to the known_diff.py file, selecting True or False\n"
                "depending on your decision:\n\n"
                "  CLAML_VS_SCRAPED_DIFFERENCES = KnownDifferences(\n"
                "    claml_only={\n"
                "       ..."
            )
            for code in unknown_claml_only_codes:
                print(
                    f'       "{code}": CodeDifference(include_in_release=True/False),'
                )
            print("    }")
            print("    ...")
            print("  )\n")
        if unknown_scraped_only_codes:
            print(
                "\nScraped-only codes\n------------------\n"
                "There are codes in the scraped, but not in the CLAML. This could be:\n"
                " - A code that was added to the scraped but not the CLAML\n"
                " - A code has been removed from the CLAML but not the scraped\n\n"
                "Once you've decided whether you want to include or exclude each one below,\n"
                "add the following to the known_diff.py file, selecting True or False\n"
                "depending on your decision:\n\n"
                "  CLAML_VS_SCRAPED_DIFFERENCES = KnownDifferences(\n"
                "    ...\n"
                "    scraped_only={\n"
                "      ..."
            )
            for code in unknown_scraped_only_codes:
                print(
                    f'       "{code}": CodeDifference(include_in_release=True/False),'
                )
            print("    }")
            print("    ...")
            print("  )\n")
        if unknown_term_differences:
            print(
                "\nDescription (term) differences\n------------------------------\n"
                "There are codes whose descriptions (terms) differ between the CLAML and scraped.\n\n"
                "Review each code below. In most cases, we should take the scraped description\n"
                "as that is what the backend data is coded with. Once you've decided which\n"
                "description to use, add it to the known_diff.py file as follows:\n\n"
                "  CLAML_VS_SCRAPED_DIFFERENCES = KnownDifferences(\n"
                "    ...\n"
                "    term_differences={\n"
                "      ..."
            )
            for code, claml_term, scraped_term in unknown_term_differences:
                print(f'      "{code}": TermDifference(')
                print(f'        claml="{claml_term}",')
                print(f'        scraped="{scraped_term}",')
                print('        use="claml|scraped",')
                print("      ),")
            print("    }")
            print("  )\n")
        print(
            "❌❌❌ UNKNOWN DIFFS FOUND: see above for details ❌❌❌\n",
        )
    return False


def main() -> None:
    claml_xml = download_release(year="2016")
    claml_codes, place_modifiers = parse_claml(claml_xml)
    claml_records = apply_nhs_2016_alterations(
        claml_codes,
        place_modifiers,
    )
    scraped_records, _ = parse_claml(SCRAPED_CLAML)
    if not diff_records(claml_records, scraped_records, print_output=True):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
