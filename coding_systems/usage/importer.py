"""Base class for importing coding system usage data.

Different coding systems publish usage data with different page structures,
download URLs, and file formats. This base class defines the interface that
all usage importers must implement.
"""

import io
from abc import ABC, abstractmethod

import structlog
from django.db import transaction

from coding_systems.usage.models import CodeUsageEntry, CodeUsageRelease


logger = structlog.get_logger()


class UsageImporter(ABC):
    """Abstract base class for importing coding system usage data.

    Subclasses must implement the abstract methods to define the specific
    scraping logic, URL patterns, and file parsing for their coding system.
    """

    coding_system: str

    @abstractmethod
    def get_available_periods(self, session):
        """Discover and return all available periods.

        Should scrape the publication index page or equivalent and return
        a sorted list of period identifiers (strings).

        Args:
            session: requests.Session for making HTTP requests

        Returns:
            Sorted list of period identifiers, e.g. ["2023-24", "2022-23", ...]
        """
        pass

    @abstractmethod
    def get_page_url(self, period):
        """Return the publication page URL for a period.

        For coding systems that group multiple periods on one page
        (e.g. SNOMED pre-2019), this should return the shared page URL.

        Args:
            period: Period identifier string

        Returns:
            Full URL to the publication page for this period
        """
        pass

    @abstractmethod
    def find_txt_download_url(self, period, session):
        """Scrape the publication page and find the download URL.

        Must raise an exception (RequestException, HTTPError, or RuntimeError)
        if the page cannot be retrieved or the download link cannot be found.
        This allows failures to propagate to the caller for proper error handling.

        Args:
            period: Period identifier string
            session: requests.Session for making HTTP requests

        Returns:
            Full URL to the .txt file download

        Raises:
            requests.RequestException: On network errors
            requests.HTTPError: On bad HTTP responses
            RuntimeError: If the expected download link is not found
        """
        pass

    @abstractmethod
    def parse_usage_file(self, fileobj):
        """Parse a usage file and yield (code, usage) tuples.

        Args:
            fileobj: File-like object containing the usage data

        Yields:
            Tuples of (code, usage) where usage may be None
        """
        pass

    def import_period(self, period, download_url, session, batch_size=5000):
        """Download and import a single period into the database.

        This method orchestrates the entire import:
        1. Check if period already exists (skip silently if so)
        2. Download the file
        3. Parse entries into memory
        4. Create release and all entries in a single transaction
           (so if entry creation fails, no orphaned release is left)

        Args:
            period: Period identifier string
            download_url: Full URL to download
            session: requests.Session for making HTTP requests
            batch_size: Number of entries to batch for bulk_create

        Returns:
            True if newly imported, False if already existed

        Raises:
            Exception: Any exception from download, parsing, or DB insertion
        """
        log = logger.bind(period=period)

        if CodeUsageRelease.objects.filter(
            period=period, coding_system=self.coding_system
        ).exists():
            log.info("Period already imported, skipping")
            return False

        log.info("Downloading usage file", download_url=download_url)

        with session.get(download_url, stream=True, timeout=120) as resp:
            resp.raise_for_status()
            content = resp.content

        # Parse outside the network connection, so we can validate the file before
        # committing to the database.
        parsed_entries = list(self.parse_usage_file(io.BytesIO(content)))

        # Create release and entries in a single transaction so if either fails,
        # the database remains consistent (no orphaned releases).
        with transaction.atomic():
            release = CodeUsageRelease.objects.create(
                period=period,
                source_url=download_url,
                coding_system=self.coding_system,
            )
            entries = []
            for code, usage in parsed_entries:
                entries.append(
                    CodeUsageEntry(
                        release=release,
                        code=code,
                        usage=usage,
                    )
                )
                if len(entries) >= batch_size:
                    CodeUsageEntry.objects.bulk_create(entries)
                    entries = []
            if entries:
                CodeUsageEntry.objects.bulk_create(entries)

        log.info("Period imported", period=period, entries=len(parsed_entries))
        return True
