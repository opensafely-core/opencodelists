import pytest

from coding_systems.usage.importer import UsageImporter
from coding_systems.usage.models import CodeUsageEntry, CodeUsageRelease


CODING_SYSTEM = "snomedct"


class StubImporter(UsageImporter):
    """Minimal concrete UsageImporter for testing the base class import_period logic."""

    coding_system = CODING_SYSTEM

    def get_available_periods(self, session):  # pragma: no cover
        return []

    def get_page_url(self, period):  # pragma: no cover
        return f"https://example.com/{period}"

    def find_txt_download_url(self, period, session):  # pragma: no cover
        return f"https://example.com/{period}.txt"

    def parse_usage_file(self, fileobj):
        # Simple two-column TSV: code<tab>usage
        for line in fileobj.read().decode().splitlines()[1:]:
            parts = line.split("\t")
            cid, raw = parts[0], parts[1]
            yield cid, None if raw == "*" else int(raw)


class DummyResponse:
    def __init__(self, content=b""):
        self.content = content

    def raise_for_status(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class DummySession:
    def __init__(self, url, content):
        self._url = url
        self._content = content

    def get(self, url, **kwargs):
        assert url == self._url
        return DummyResponse(content=self._content)


@pytest.mark.django_db
def test_import_period_skips_if_release_already_exists():
    period = "2023-24"
    CodeUsageRelease.objects.create(
        coding_system=CODING_SYSTEM, period=period, source_url="https://existing"
    )
    importer = StubImporter()

    assert importer.import_period(period, "https://new.txt", session=None) is False
    assert (
        CodeUsageRelease.objects.filter(
            coding_system=CODING_SYSTEM, period=period
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_import_period_creates_release_and_entries():
    period = "2022-23"
    download_url = "https://example.com/2022-23.txt"
    file_bytes = b"code\tusage\n100\t10\n200\t*\n300\t1500\n"
    session = DummySession(download_url, file_bytes)
    importer = StubImporter()

    assert (
        importer.import_period(period, download_url, session=session, batch_size=2)
        is True
    )

    release = CodeUsageRelease.objects.get(coding_system=CODING_SYSTEM, period=period)
    assert release.source_url == download_url

    entries = list(CodeUsageEntry.objects.filter(release=release).order_by("code"))
    assert [(e.code, e.usage) for e in entries] == [
        ("100", 10),
        ("200", None),
        ("300", 1500),
    ]
