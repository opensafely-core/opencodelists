NHS_2016_ONLY_CODES = {
    # Currently no codes that only appear in the scraped data but keeping
    # the property here in case we want to add some in future
}


def is_2016_scraped_only(code: str) -> bool:
    """Check if a code is expected to be only in the 2016 scraped data."""
    return code in NHS_2016_ONLY_CODES


def should_include_2016_scraped_only(code: str) -> bool:
    """For a scraped-only code, check if it should be included in the release."""
    known = NHS_2016_ONLY_CODES.get(code)
    return known is not None and known.include_in_release
