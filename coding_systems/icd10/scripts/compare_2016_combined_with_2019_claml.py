"""
Compare a merged ICD-10 2016 record set with WHO ICD-10 2019 ClaML.

The merged 2016 set is built from WHO 2016 ClaML and scraped NHS Class Browser
2016 ClaML using the decisions recorded in known_diffs.py.

Usage:

    python -m coding_systems.icd10.scripts.compare_2016_combined_with_2019_claml
"""

from pathlib import Path

from coding_systems.icd10.claml_parser import ICD10Code, parse_claml
from coding_systems.icd10.data_downloader import download_release
from coding_systems.icd10.known_diffs import (
    apply_nhs_2016_alterations,
    include_2016_claml_only,
    include_2016_scraped_only,
    is_2016_2019_clinically_different_description_difference,
    is_2016_2019_clinically_equivalent_description_difference,
    is_2016_2019_description_difference,
    use_scraped_for_2016,
)
from coding_systems.icd10.scripts.compare_2016_claml_with_scraped import diff_records


ICD10_ROOT = Path(__file__).parent.parent
RELEASE_DIR = ICD10_ROOT / "data"
SCRAPED_CLAML = RELEASE_DIR / "scraped_classbrowser_2016.xml"


def _description_with_modifier(record: ICD10Code) -> str:
    if record.term_modifier:
        return f"{record.description} ({record.term_modifier})"
    return record.description


def merge_2016_records(
    claml_records: dict[str, ICD10Code],
    scraped_records: dict[str, ICD10Code],
) -> dict[str, ICD10Code]:
    merged: dict[str, ICD10Code] = {}
    all_codes = sorted(set(claml_records) | set(scraped_records))

    for code in all_codes:
        claml_record = claml_records.get(code)
        scraped_record = scraped_records.get(code)

        if claml_record is None and include_2016_scraped_only(code):
            merged[code] = scraped_record
            continue

        if scraped_record is None and include_2016_claml_only(code):
            merged[code] = claml_record
            continue

        claml_description = _description_with_modifier(claml_record)
        scraped_description = _description_with_modifier(scraped_record)
        if claml_description == scraped_description:
            merged[code] = scraped_record
            continue

        merged[code] = scraped_record if use_scraped_for_2016(code) else claml_record

    return merged


def diff_2016_with_2019(
    combined_2016_records: dict[str, ICD10Code],
    who_2019_records: dict[str, ICD10Code],
) -> bool:
    combined_2016_codes = set(combined_2016_records)
    who_2019_codes = set(who_2019_records)

    combined_2016_only_codes = sorted(combined_2016_codes - who_2019_codes)
    who_2019_only_codes = sorted(who_2019_codes - combined_2016_codes)

    clinically_equivalent_description_difference_count = 0
    clinically_different_description_difference_count = 0
    unknown_description_differences = []
    for code in sorted(combined_2016_codes & who_2019_codes):
        combined_2016_description = _description_with_modifier(
            combined_2016_records[code]
        )
        who_2019_description = _description_with_modifier(who_2019_records[code])
        if combined_2016_description == who_2019_description:
            continue

        if is_2016_2019_clinically_equivalent_description_difference(
            code,
            combined_2016_description,
            who_2019_description,
        ):
            clinically_equivalent_description_difference_count += 1
        elif is_2016_2019_clinically_different_description_difference(
            code,
            combined_2016_description,
            who_2019_description,
        ):
            clinically_different_description_difference_count += 1

        if not is_2016_2019_description_difference(
            code,
            combined_2016_description,
            who_2019_description,
        ):
            unknown_description_differences.append(
                (code, combined_2016_description, who_2019_description)
            )

    description_difference_count = (
        clinically_equivalent_description_difference_count
        + clinically_different_description_difference_count
        + len(unknown_description_differences)
    )

    print(
        "\n\nCompared combined 2016 ICD-10 records with WHO 2019 ClaML\n\n"
        f"Combined 2016 records: {len(combined_2016_records)}\n"
        f"WHO 2019 records:     {len(who_2019_records)}\n\n"
        "Summary\n-------\n"
        f"Combined 2016-only codes: {len(combined_2016_only_codes)}\n"
        f"WHO 2019-only codes:      {len(who_2019_only_codes)}\n"
        f"Description changes:      {description_difference_count} (of which {len(unknown_description_differences)} unknown)\n"
        f"  Clinically equivalent:  {clinically_equivalent_description_difference_count}\n"
        f"  Clinically different:   {clinically_different_description_difference_count}"
    )

    if not unknown_description_differences:
        print("\n✅ ALL OK: every difference is expected\n")
        return True

    if unknown_description_differences:
        print(
            "\nDescription (term) differences\n------------------------------\n"
            "There are codes whose descriptions differ between combined 2016 and WHO 2019.\n"
            "Review whether each difference is clinically equivalent or clinically different,\n"
            "then add it to known_diffs.py as follows:\n\n"
            "  COMBINED_2016_VS_2019_DIFFERENCES = {\n"
            "    ..."
        )
        for code, combined_2016_term, who_2019_term in unknown_description_differences:
            print(f'    "{code}": ReleaseTermDifference(')
            print(f'      combined_2016="{combined_2016_term}",')
            print(f'      who_2019="{who_2019_term}",')
            print("      clinically_equivalent=True/False,")
            print("    ),")
        print("  }\n")

    print(
        "❌❌❌ UNKNOWN DIFFS FOUND: see above for details ❌❌❌\n",
    )
    return False


def main() -> None:
    claml_2016_xml = download_release(year="2016")
    claml_2019_xml = download_release(year="2019")

    codes_2016, place_modifiers = parse_claml(claml_2016_xml)
    claml_2016_records = apply_nhs_2016_alterations(
        codes_2016,
        place_modifiers,
    )
    scraped_2016_records, _ = parse_claml(SCRAPED_CLAML)

    if not diff_records(claml_2016_records, scraped_2016_records):
        print(
            "\n❌❌❌ UNKNOWN DIFFS FOUND BETWEEN 2016 CLAML AND SCRAPED ❌❌❌\n"
            "Please run TODO compare_2016_claml_with_scraped.py and resolve any"
            "unknown differences before comparing with 2019 ClaML"
        )
        return

    combined_2016_records = merge_2016_records(
        claml_2016_records,
        scraped_2016_records,
    )
    claml_2019_records, _ = parse_claml(claml_2019_xml)

    if not diff_2016_with_2019(
        combined_2016_records,
        claml_2019_records,
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
