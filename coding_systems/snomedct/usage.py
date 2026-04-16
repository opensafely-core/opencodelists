"""SNOMED CT usage data importer for NHS Digital source."""

import csv
import io
import re

from bs4 import BeautifulSoup

from coding_systems.usage.importer import UsageImporter


BASE_URL = "https://digital.nhs.uk/data-and-information/publications/statistical/mi-snomed-code-usage-in-primary-care"

# Pre-2019 periods share one publication page; each period since 2018-19 has its own.
MULTI_YEAR_PAGE_SLUG = "2011-12-to-2017-18"
MULTI_YEAR_PERIODS = [
    "2011-12",
    "2012-13",
    "2013-14",
    "2014-15",
    "2015-16",
    "2016-17",
    "2017-18",
]

_SINGLE_PERIOD_RE = re.compile(r"/\d{4}-\d{2}$")
CODING_SYSTEM = "snomedct"


class SnomedUsageImporter(UsageImporter):
    """Importer for NHS Digital SNOMED code usage data.

    Files are published annually at:
      https://digital.nhs.uk/data-and-information/publications/statistical/mi-snomed-code-usage-in-primary-care

    Periods from 2011-12 to 2017-18 share a single publication page as these all
    predate SNOMED in primary care and so have been mapped from Readv2 and CTV3.
    Each year since 2018-19 has its own page. File URLs are not predictable, so
    we scrape each publication page to locate the .txt download link.
    """

    coding_system = CODING_SYSTEM

    def get_available_periods(self, session):
        """Scrape the NHS Digital index page and return all published periods."""
        resp = session.get(BASE_URL, timeout=30)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        periods = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.endswith(MULTI_YEAR_PAGE_SLUG):
                periods.update(MULTI_YEAR_PERIODS)
            elif _SINGLE_PERIOD_RE.search(href):
                periods.add(href.split("/")[-1])
        return sorted(periods)

    def get_page_url(self, period):
        """Return the NHS Digital publication page URL for *period*."""
        if period in MULTI_YEAR_PERIODS:
            return f"{BASE_URL}/{MULTI_YEAR_PAGE_SLUG}"
        return f"{BASE_URL}/{period}"

    def find_txt_download_url(self, period, session):
        """Scrape the publication page for *period* and return the .txt download URL.

        Raises ``requests.RequestException`` on network errors, ``requests.HTTPError``
        on bad HTTP responses, and ``RuntimeError`` if the expected download link is
        not found on the page.
        """
        page_url = self.get_page_url(period)

        resp = session.get(page_url, timeout=30)
        resp.raise_for_status()

        filename = f"SNOMED_code_usage_{period}.txt"
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", href=True):
            if a["href"].endswith(filename):
                return a["href"]

        raise RuntimeError(
            f"Could not find .txt download link on publication page for {period}"
        )

    def parse_usage_file(self, fileobj):
        """Parse a TSV usage file and yield ``(code, usage)`` tuples.

        ``usage`` is ``None`` for entries marked ``*`` (fewer than 5 uses).
        """
        reader = csv.DictReader(
            io.TextIOWrapper(fileobj, encoding="utf-8"), delimiter="\t"
        )
        for row in reader:
            result = self._parse_usage_row(row)
            if result is not None:
                yield result

    @staticmethod
    def _parse_usage_row(row):
        """Parse a single TSV row, returning (code, usage) or None for blank rows."""
        cid = row.get("SNOMED_Concept_ID", "").strip()
        if not cid:
            return None
        usage_val = row.get("Usage", "").strip()
        if usage_val == "*":
            return cid, None
        try:
            return cid, int(usage_val.replace(",", ""))
        except ValueError:
            raise ValueError(
                f"Unrecognised usage value {usage_val!r} for SNOMED concept {cid}"
            )
