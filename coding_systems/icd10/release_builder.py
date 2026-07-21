from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import structlog

from coding_systems.icd10.claml_parser import (
    ICD10Code,
    ModifierDigit,
    parse_claml,
)
from coding_systems.icd10.data_downloader import Year
from coding_systems.icd10.known_diffs import (
    KNOWN_2016_RUBRIC_CHANGES,
    expand_who_2016_place_of_occurrence,
    get_2016_2019_description_difference,
    is_2016_claml_only,
    is_2016_description_difference,
    is_2016_scraped_only,
    should_include_2016_claml_only,
    should_include_2016_scraped_only,
    should_use_scraped_for_2016,
)


ICD10_ROOT = Path(__file__).parent
DATA_DIR = ICD10_ROOT / "data"
SCRAPED_2016_CLAML = DATA_DIR / "scraped_classbrowser_2016.xml"

logger = structlog.get_logger()


@dataclass(frozen=True, slots=True)
class Claml2016ScrapedDiffReport:
    """Summary of differences between WHO 2016 ClaML and scraped NHS 2016 ClaML."""

    claml_record_count: int
    scraped_record_count: int
    claml_only_codes: list[str]
    scraped_only_codes: list[str]
    unexpected_claml_only_codes: list[str]
    unexpected_scraped_only_codes: list[str]
    description_difference_count: int
    unexpected_term_differences: list[tuple[str, str, str]]

    @property
    def has_unexpected_differences(self) -> bool:
        return any(
            (
                self.unexpected_claml_only_codes,
                self.unexpected_scraped_only_codes,
                self.unexpected_term_differences,
            )
        )


@dataclass(frozen=True, slots=True)
class Combined2016Claml2019ReleaseDiffReport:
    """Summary of term differences between combined 2016 records and WHO 2019."""

    combined_2016_record_count: int
    who_2019_record_count: int
    combined_2016_only_codes: list[str]
    who_2019_only_codes: list[str]
    clinically_equivalent_description_difference_count: int
    clinically_different_description_difference_count: int
    unexpected_description_differences: list[tuple[str, str, str]]

    @property
    def description_difference_count(self) -> int:
        return (
            self.clinically_equivalent_description_difference_count
            + self.clinically_different_description_difference_count
            + len(self.unexpected_description_differences)
        )

    @property
    def has_unexpected_differences(self) -> bool:
        return bool(self.unexpected_description_differences)


def apply_nhs_2016_alterations(
    records: dict[str, ICD10Code],
    place_modifiers: list[ModifierDigit],
) -> dict[str, ICD10Code]:
    """
    There are known alterations to the WHO 2016 release applied by the NHS. Currently
    this is just the treatment of place of occurrence modifiers for 3 ICD10 codes. See
    the comments in the known_diffs.py file for details.
    """
    altered_records = dict(records)

    place_records = expand_who_2016_place_of_occurrence(
        altered_records, place_modifiers
    )
    altered_records.update(place_records)

    return altered_records


def build_2016_claml_scraped_diff_report(
    claml_records: dict[str, ICD10Code], scraped_records: dict[str, ICD10Code]
) -> Claml2016ScrapedDiffReport:
    """
    Compare WHO 2016 ClaML records with scraped NHS 2016 records.

    Returns a report object. Differences are marked unexpected
    unless they are recorded in known_diffs.py.
    """
    claml_codes = set(claml_records)
    scraped_codes = set(scraped_records)

    claml_only_codes = sorted(claml_codes - scraped_codes)
    scraped_only_codes = sorted(scraped_codes - claml_codes)
    codes_in_both = sorted(claml_codes & scraped_codes)

    unexpected_claml_only_codes = [
        code for code in claml_only_codes if not is_2016_claml_only(code)
    ]
    unexpected_scraped_only_codes = [
        code for code in scraped_only_codes if not is_2016_scraped_only(code)
    ]

    unexpected_term_differences = []
    description_difference_count = 0
    for code in codes_in_both:
        claml_description = claml_records[code].short_term_with_modifier
        scraped_description = scraped_records[code].term_with_modifier
        if claml_description == scraped_description:
            continue

        description_difference_count += 1

        if not is_2016_description_difference(
            code,
            claml_description,
            scraped_description,
        ):
            unexpected_term_differences.append(
                (code, claml_description, scraped_description)
            )

    return Claml2016ScrapedDiffReport(
        claml_record_count=len(claml_records),
        scraped_record_count=len(scraped_records),
        claml_only_codes=claml_only_codes,
        scraped_only_codes=scraped_only_codes,
        unexpected_claml_only_codes=unexpected_claml_only_codes,
        unexpected_scraped_only_codes=unexpected_scraped_only_codes,
        description_difference_count=description_difference_count,
        unexpected_term_differences=unexpected_term_differences,
    )


def print_2016_claml_scraped_diff_report(report: Claml2016ScrapedDiffReport) -> None:
    """Print the 2016 CLAML-vs-scraped diff summary and remediation snippets."""
    logger.info(
        "\n\nCompared WHO 2016 ClaML with scraped NHS Class Browser 2016 ClaML\n\n"
        f"CLAML records:   {report.claml_record_count}\n"
        f"Scraped records: {report.scraped_record_count}\n\n"
        "Summary\n-------\n"
        f"CLAML-only codes:  {len(report.claml_only_codes)} (of which {len(report.unexpected_claml_only_codes)} unexpected)\n"
        f"Scraped-only codes:  {len(report.scraped_only_codes)} (of which {len(report.unexpected_scraped_only_codes)} unexpected)\n"
        f"Description changes:  {report.description_difference_count} (of which {len(report.unexpected_term_differences)} unexpected)"
    )

    if not report.has_unexpected_differences:
        logger.info("\n✅ ALL OK: every difference is expected\n")
        return

    if report.unexpected_claml_only_codes:
        logger.error(
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
        for code in report.unexpected_claml_only_codes:
            logger.error(
                f'       "{code}": CodeDifference(include_in_release=True/False),'
            )
        logger.error("    }")
        logger.error("    ...")
        logger.error("  )\n")
    if report.unexpected_scraped_only_codes:
        logger.error(
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
        for code in report.unexpected_scraped_only_codes:
            logger.error(
                f'       "{code}": CodeDifference(include_in_release=True/False),'
            )
        logger.error("    }")
        logger.error("    ...")
        logger.error("  )\n")
    if report.unexpected_term_differences:
        logger.error(
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
        for code, claml_term, scraped_term in report.unexpected_term_differences:
            logger.error(f'      "{code}": TermDifference(')
            logger.error(f'        claml="{claml_term}",')
            logger.error(f'        scraped="{scraped_term}",')
            logger.error('        use="claml|scraped",')
            logger.error("      ),")
        logger.error("    }")
        logger.error("  )\n")
    logger.error(
        "❌❌❌ UNEXPECTED DIFFS FOUND: see above for details ❌❌❌\n",
    )


def check_diff_2016_claml_with_scraped(
    claml_records: dict[str, ICD10Code], scraped_records: dict[str, ICD10Code]
) -> None:
    """
    Print and enforce the known-difference check for 2016 source records.

    Raises ValueError if WHO 2016 ClaML and scraped NHS 2016 records contain
    differences that are not recorded in known_diffs.py.
    """
    report = build_2016_claml_scraped_diff_report(claml_records, scraped_records)
    print_2016_claml_scraped_diff_report(report)
    if not report.has_unexpected_differences:
        return

    raise ValueError(
        "Unexpected differences found between 2016 CLAML and scraped records.\n"
        "See output for details and update coding_systems/icd10/known_diffs.py to resolve."
    )


def _check_rubrics(code: str, record: ICD10Code) -> None:
    if code in KNOWN_2016_RUBRIC_CHANGES:
        change = KNOWN_2016_RUBRIC_CHANGES[code]
        if record.concept_rubrics != change.who_2016:
            raise ValueError(
                f"Unexpected rubric for {code}: {record.concept_rubrics!r} "
                f"(expected {change.who_2016!r})"
            )


def _change_rubrics(code: str, record: ICD10Code) -> ICD10Code:
    if code in KNOWN_2016_RUBRIC_CHANGES:
        change = KNOWN_2016_RUBRIC_CHANGES[code]
        record.concept_rubrics = change.resolved_rubrics
    return record


def _merge_2016_claml_and_scraped_records(
    claml_2016_records: dict[str, ICD10Code],
    scraped_2016_records: dict[str, ICD10Code],
) -> dict[str, ICD10Code]:
    """
    Merge already-validated WHO 2016 and scraped NHS 2016 records.

    When a code exists in both sources, the should_use_scraped_for_2016 helper is
    used to decide which description to use in the combined 2016 records.
    """
    combined: dict[str, ICD10Code] = {}
    for code in sorted(set(claml_2016_records) | set(scraped_2016_records)):
        claml_record = claml_2016_records.get(code)
        scraped_record = scraped_2016_records.get(code)

        _check_rubrics(code, claml_record)
        claml_record = _change_rubrics(code, claml_record) if claml_record else None
        scraped_record = (
            _change_rubrics(code, scraped_record) if scraped_record else None
        )

        if claml_record is None:
            if should_include_2016_scraped_only(code):
                combined[code] = scraped_record
            continue

        if scraped_record is None:
            if should_include_2016_claml_only(code):
                combined[code] = claml_record
            continue

        claml_description_short = claml_record.short_term_with_modifier
        scraped_description = scraped_record.term_with_modifier
        if claml_description_short == scraped_description:
            # The browser only has the short description so we compare on that. If they match,
            # we can take the CLAML record as the source of truth for the long description.
            combined[code] = claml_record
            continue

        combined[code] = (
            scraped_record if should_use_scraped_for_2016(code) else claml_record
        )

    return combined


def combine_2016_claml_and_scraped_records(
    who_2016_records, scraped_2016_records
) -> dict[str, ICD10Code]:
    """
    Build the combined 2016 ICD-10 records from WHO ClaML and scraped NHS data.

    Raises ValueError if the two sources contain unexpected differences.
    """
    check_diff_2016_claml_with_scraped(who_2016_records, scraped_2016_records)
    return _merge_2016_claml_and_scraped_records(who_2016_records, scraped_2016_records)


def build_2016_2019_diff_report(
    combined_2016_records: dict[str, ICD10Code],
    who_2019_records: dict[str, ICD10Code],
) -> Combined2016Claml2019ReleaseDiffReport:
    """
    Compare combined 2016 records with WHO 2019 records.

    Returns a report object. Description differences are classified
    from known_diffs.py.
    """
    combined_2016_codes = set(combined_2016_records)
    who_2019_codes = set(who_2019_records)

    combined_2016_only_codes = sorted(combined_2016_codes - who_2019_codes)
    who_2019_only_codes = sorted(who_2019_codes - combined_2016_codes)
    codes_in_both = sorted(combined_2016_codes & who_2019_codes)

    clinically_equivalent_description_difference_count = 0
    clinically_different_description_difference_count = 0

    unexpected_description_differences = []

    for code in codes_in_both:
        combined_2016_description = combined_2016_records[code].term_with_modifier
        who_2019_description = who_2019_records[code].term_with_modifier
        if combined_2016_description == who_2019_description:
            continue

        known_diff = get_2016_2019_description_difference(
            code,
            combined_2016_description,
            who_2019_description,
        )
        if known_diff is None:
            unexpected_description_differences.append(
                (code, combined_2016_description, who_2019_description)
            )
        elif known_diff.clinically_equivalent:
            clinically_equivalent_description_difference_count += 1
        else:
            clinically_different_description_difference_count += 1

    return Combined2016Claml2019ReleaseDiffReport(
        combined_2016_record_count=len(combined_2016_records),
        who_2019_record_count=len(who_2019_records),
        combined_2016_only_codes=combined_2016_only_codes,
        who_2019_only_codes=who_2019_only_codes,
        clinically_equivalent_description_difference_count=(
            clinically_equivalent_description_difference_count
        ),
        clinically_different_description_difference_count=(
            clinically_different_description_difference_count
        ),
        unexpected_description_differences=unexpected_description_differences,
    )


def print_2016_2019_diff_report(report: Combined2016Claml2019ReleaseDiffReport) -> None:
    """Print the combined-2016-vs-WHO-2019 diff summary and remediation snippets."""
    logger.info(
        "\n\nCompared combined 2016 ICD-10 records with WHO 2019 ClaML\n\n"
        f"Combined 2016 records: {report.combined_2016_record_count}\n"
        f"WHO 2019 records:     {report.who_2019_record_count}\n\n"
        "Summary\n-------\n"
        f"Combined 2016-only codes: {len(report.combined_2016_only_codes)}\n"
        f"WHO 2019-only codes:      {len(report.who_2019_only_codes)}\n"
        f"Description changes:      {report.description_difference_count} (of which {len(report.unexpected_description_differences)} unexpected)\n"
        f"  Clinically equivalent:  {report.clinically_equivalent_description_difference_count}\n"
        f"  Clinically different:   {report.clinically_different_description_difference_count}"
    )

    if not report.has_unexpected_differences:
        logger.info("\n✅ ALL OK: every difference is expected\n")
        return

    logger.error(
        "\nDescription (term) differences\n------------------------------\n"
        "There are codes whose descriptions differ between combined 2016 and WHO 2019.\n"
        "Review whether each difference is clinically equivalent or clinically different,\n"
        "then add it to known_diffs.py as follows:\n\n"
        "  COMBINED_2016_VS_2019_DIFFERENCES = {\n"
        "    ..."
    )
    for (
        code,
        combined_2016_term,
        who_2019_term,
    ) in report.unexpected_description_differences:
        logger.error(f'    "{code}": ReleaseTermDifference(')
        logger.error(f'      combined_2016="{combined_2016_term}",')
        logger.error(f'      who_2019="{who_2019_term}",')
        logger.error("      clinically_equivalent=True/False,")
        logger.error("    ),")
    logger.error("  }\n")

    logger.error(
        "❌❌❌ UNEXPECTED DIFFS FOUND: see above for details ❌❌❌\n",
    )


def check_diff_2016_with_2019(
    combined_2016_records: dict[str, ICD10Code],
    who_2019_records: dict[str, ICD10Code],
) -> None:
    """
    Print and enforce the known-difference check for 2016 and 2019 records.

    Raises ValueError if combined 2016 records and WHO 2019 records contain
    term differences that are not recorded in known_diffs.py.
    """
    report = build_2016_2019_diff_report(combined_2016_records, who_2019_records)
    print_2016_2019_diff_report(report)
    if not report.has_unexpected_differences:
        return

    raise ValueError(
        "Unexpected differences found between combined 2016 and WHO 2019 releases.\n"
        "See output for details and update coding_systems/icd10/known_diffs.py to resolve."
    )


def load_import_records(
    release_zipfile, file_metadata
) -> tuple[dict[str, ICD10Code], dict[str, ICD10Code]]:
    """
    Build the parsed ICD-10 record sets used by the importer.

    Returns the combined 2016 records and WHO 2019 records. Raises ValueError
    if any release source differences are not recorded in known_diffs.py.
    """
    with TemporaryDirectory() as tempdir:
        release_zip = ZipFile(release_zipfile)
        logger.info("Extracting", release_zip=release_zip.filename)
        release_zip.extractall(path=tempdir)

        release_dir = Path(tempdir)
        xml_path_2016 = release_dir / file_metadata[Year.WHO_2016.name]["xml_filename"]
        xml_path_2019 = release_dir / file_metadata[Year.WHO_2019.name]["xml_filename"]
        xml_path_nhs = release_dir / file_metadata[Year.NHS_2016.name]["xml_filename"]

        # We apply known NHS alterations to the base WHO 2016 ClaML records
        # before comparing with the scraped NHS 2016 records.
        codes_2016, place_modifiers = parse_claml(xml_path_2016)
        output_who_2016 = apply_nhs_2016_alterations(codes_2016, place_modifiers)

        output_who_2019, _ = parse_claml(xml_path_2019)
        output_nhs_2016, _ = parse_claml(xml_path_nhs)

    output_combined_2016 = combine_2016_claml_and_scraped_records(
        output_who_2016, output_nhs_2016
    )
    check_diff_2016_with_2019(output_combined_2016, output_who_2019)

    return output_combined_2016, output_who_2019
