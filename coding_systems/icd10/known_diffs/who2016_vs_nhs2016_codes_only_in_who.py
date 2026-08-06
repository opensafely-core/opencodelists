from coding_systems.icd10.known_diffs.difference_classes import CodeDifference


WHO_2016_ONLY_CODES: dict[str, CodeDifference] = {
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
}


def is_2016_claml_only(code: str) -> bool:
    """Check if a code is expected to be only in the 2016 CLAML data."""
    return code in WHO_2016_ONLY_CODES


def should_include_2016_claml_only(code: str) -> bool:
    """For a ClAML-only code, check if it should be included in the release."""
    known = WHO_2016_ONLY_CODES.get(code)
    return known is not None and known.include_in_release
