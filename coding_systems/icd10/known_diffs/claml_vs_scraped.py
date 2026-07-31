from .difference_classes import CodeDifference, KnownDifferences, TermDifference


# Known differences between the 2016 WHO ICD10 claml and the scraped ICD10
# data from the NHS class browser
CLAML_VS_SCRAPED_DIFFERENCES = KnownDifferences(
    claml_only={
        # The CLAML says you can apply the 5th char modifier to M14.*, but
        # doesn't say you can in any online version. It also doesn't appear
        # in the backend data. But no harm in including, and it is technically
        # in the XML, so we keep it. The 5th char modifiers are 0-9 and apply
        # to M140-M146 and M148-M149, but not M147 which doesn't exist
        **{
            f"M{i}": CodeDifference(include_in_release=True)
            for i in list(range(1400, 1470)) + list(range(1480, 1490))
        },
        # W00-Y34 (except Y06 and Y07) are all 3 char codes in the CLAML,
        # which the NHS allows a 4th character "place of occurrence" modifier.
        # The online browser metnions this, but not in a structure way so
        # the scraper doesn't pick it up. We therefore expect all codes
        # in that range to be in the claml but not the scraped data.
        # W000-W999
        **{
            f"W{number:03d}": CodeDifference(include_in_release=True)
            for number in range(0, 1000)
        },
        # X000-X999
        **{
            f"X{number:03d}": CodeDifference(include_in_release=True)
            for number in range(0, 1000)
        },
        # Y000-Y349 (except Y06 and Y07)
        **{
            f"Y{number:03d}": CodeDifference(include_in_release=True)
            for number in list(range(0, 600)) + list(range(800, 3500))
        },
    },
    scraped_only={
        # Currently no codes that only appear in the scraped data but keeping
        # the property here in case we want to add some in future
    },
    term_differences={
        # The expected differences in the terms between the CLAML and scraped
        # data, and which one we want to use in the release. The scraped term
        # is usually the one we prefer as we're trying to match the NHS classbrowser
        # as closely as possible, but in some cases the CLAML term is better.
        "J10": TermDifference(
            claml="influenza due to identified seasonal influenza virus",
            scraped="Influenza due to identified seasonal influenza virus",
            use="scraped",
        ),
        "P710": TermDifference(
            claml="Cow milk hypocalcaemia in newborn",
            scraped="Cow's milk hypocalcaemia in newborn",
            use="scraped",
        ),
        "U06": TermDifference(
            claml="Zika virus disease",
            scraped="Emergency use of U06",
            use="claml",
            # U06 isn't a code you can actually use (as it has 4 char children) so
            # the NHS haven't updated it. So the claml version is more accurate
            # now that U609 is Zika virus instead of emergency use
        ),
        "U069": TermDifference(
            claml="Zika virus disease, unspecified",
            scraped="Zika virus disease",
            use="scraped",
        ),
        "U070": TermDifference(
            claml="Emergency use of U07.0",
            scraped="Vaping-related disorder",
            use="scraped",
        ),
        "U071": TermDifference(
            claml="Emergency use of U07.1",
            scraped="COVID-19, virus identified",
            use="scraped",
        ),
        "U072": TermDifference(
            claml="Emergency use of U07.2",
            scraped="COVID-19, virus not identified",
            use="scraped",
        ),
        "U073": TermDifference(
            claml="Emergency use of U07.3",
            scraped="Personal history of COVID-19",
            use="scraped",
        ),
        "U074": TermDifference(
            claml="Emergency use of U07.4",
            scraped="Post COVID-19 condition",
            use="scraped",
        ),
        "U075": TermDifference(
            claml="Emergency use of U07.5",
            scraped="Multisystem inflammatory syndrome associated with COVID-19",
            use="scraped",
        ),
        "U076": TermDifference(
            claml="Emergency use of U07.6",
            scraped="Need for immunization against COVID-19",
            use="scraped",
        ),
        "U077": TermDifference(
            claml="Emergency use of U07.7",
            scraped="COVID-19 vaccines causing adverse effects in therapeutic use",
            use="scraped",
        ),
    },
)


def is_2016_claml_only(code: str) -> bool:
    """Check if a code is expected to be only in the 2016 CLAML data."""
    return code in CLAML_VS_SCRAPED_DIFFERENCES.claml_only


def is_2016_scraped_only(code: str) -> bool:
    """Check if a code is expected to be only in the 2016 scraped data."""
    return code in CLAML_VS_SCRAPED_DIFFERENCES.scraped_only


def is_2016_description_difference(
    code: str,
    claml_description: str,
    scraped_description: str,
) -> bool:
    """Check if a code is expected to have a different description in the 2016 CLAML vs scraped data."""
    known = CLAML_VS_SCRAPED_DIFFERENCES.term_differences.get(code)
    return (
        known is not None
        and known.claml == claml_description
        and known.scraped == scraped_description
    )


def should_include_2016_claml_only(code: str) -> bool:
    """For a ClAML-only code, check if it should be included in the release."""
    known = CLAML_VS_SCRAPED_DIFFERENCES.claml_only.get(code)
    return known is not None and known.include_in_release


def should_include_2016_scraped_only(code: str) -> bool:
    """For a scraped-only code, check if it should be included in the release."""
    known = CLAML_VS_SCRAPED_DIFFERENCES.scraped_only.get(code)
    return known is not None and known.include_in_release


def should_use_scraped_for_2016(code: str) -> bool:
    """For a code with a description difference, should we use the scraped description?"""
    known = CLAML_VS_SCRAPED_DIFFERENCES.term_differences.get(code)
    return known is not None and known.use == "scraped"
