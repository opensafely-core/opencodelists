from coding_systems.icd10.known_diffs.difference_classes import TermDifference


WHO_2016_NHS_2016_TERM_DIFFERENCES: dict[str, TermDifference] = {
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
}


def is_2016_description_difference(
    code: str,
    claml_description: str,
    scraped_description: str,
) -> bool:
    """Check if a code is expected to have a different description in the 2016 CLAML vs scraped data."""
    known = WHO_2016_NHS_2016_TERM_DIFFERENCES.get(code)
    return (
        known is not None
        and known.claml == claml_description
        and known.scraped == scraped_description
    )


def should_use_scraped_for_2016(code: str) -> bool:
    """For a code with a description difference, should we use the scraped description?"""
    known = WHO_2016_NHS_2016_TERM_DIFFERENCES.get(code)
    return known is not None and known.use == "scraped"
