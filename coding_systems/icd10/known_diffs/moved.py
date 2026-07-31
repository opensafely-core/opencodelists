# Moved code sets. We flag codelists that contain only part of one of these sets,
# because the same clinical concept is represented by different codes across releases.
# These moved codes were derived from this report (https://github.com/bennettoxford/icd-browser-scraper/blob/main/claml/2016-vs-2019.md)
# which shows all the codes that appear in one set and not the other.
MOVED_CODE_SETS = (
    {
        "title": "Pneumocystosis",
        "nhs2016": ["B59"],
        "who2019": ["B485"],
        "comment": "This is B59 in 2016, but B485 in 2019.",
    },
    {
        "title": "Causalgia",
        "nhs2016": ["G564"],
        "who2019": ["G906"],
        "comment": "This is G564 in 2016, but G906 in 2019.",
    },
    {
        "title": "Irritable bowel syndrome",
        "nhs2016": ["K58", "K580", "K589"],
        "who2019": ["K58", "K581", "K582", "K583", "K588"],
        "comment": "The codes for this were K580 and K589 in 2016, but K581, K582, K583 and K588 in 2019. You likely want all these codes in your codelist. However if you are specifically looking for diarrhoea, or constipation, rather than IBS, then you may only want some but not all of these codes.",
    },
    {
        "title": "Zika virus disease",
        "nhs2016": ["U06", "U069"],
        "who2019": ["A925"],
        "comment": "This is U06/U069 in 2016, but is A925 in 2019.",
    },
    {
        "title": "Personal history of COVID-19",
        "nhs2016": ["U073"],
        "who2019": ["U08", "U089"],
        "comment": "This is U073 in 2016, but U08/U089 in 2019.",
    },
    {
        "title": "Post COVID-19 condition",
        "nhs2016": ["U074"],
        "who2019": ["U09", "U099"],
        "comment": "This is U074 in 2016, but U09/U099 in 2019.",
    },
    {
        "title": "Multisystem inflammatory syndrome associated with COVID-19",
        "nhs2016": ["U075"],
        "who2019": ["U10", "U109"],
        "comment": "This is U075 in 2016, but U10/U109 in 2019.",
    },
    {
        "title": "Need for immunization against COVID-19",
        "nhs2016": ["U076"],
        "who2019": ["U11", "U119"],
        "comment": "This is U076 in 2016, but U11/U119 in 2019.",
    },
    {
        "title": "COVID-19 vaccines causing adverse effects in therapeutic use",
        "nhs2016": ["U077"],
        "who2019": ["U12", "U129"],
        "comment": "This is U077 in 2016, but U12/U129 in 2019.",
    },
)


def moved_codes(codes: list[str]) -> list[dict]:
    """
    Given a list of codes, return a list of moved code sets that contain any of the
    codes. Each moved code set contains the title, the codes in both releases, and a
    comment explaining the change.
    """
    normalised_codes = set(code.upper() for code in codes)
    moved_codes = []
    for moved_code_set in MOVED_CODE_SETS:
        possible_codes = moved_code_set["nhs2016"] + moved_code_set["who2019"]
        if any(code in normalised_codes for code in possible_codes):
            moved_codes.append(moved_code_set)
    return moved_codes
