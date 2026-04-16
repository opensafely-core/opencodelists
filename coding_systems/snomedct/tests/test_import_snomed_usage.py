import io
from unittest.mock import patch

import pytest
import requests
from django.core.management import CommandError, call_command

from coding_systems.snomedct.usage import (
    BASE_URL,
    CODING_SYSTEM,
    SnomedUsageImporter,
)
from coding_systems.usage.models import CodeUsageEntry, CodeUsageRelease


assert CODING_SYSTEM == "snomedct"


class DummyResponse:
    def __init__(self, text="", content=b"", status_code=200):
        self.text = text
        self.content = content
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class DummySession:
    def __init__(self, responses_by_url):
        self.responses_by_url = responses_by_url
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        response = self.responses_by_url[url]
        if isinstance(response, Exception):
            raise response
        return response


def test_get_available_periods_from_absolute_and_relative_links():
    html = f"""
    <html><body>
      <a href="{BASE_URL}/2023-24">2023-24</a>
      <a href="/data-and-information/publications/statistical/mi-snomed-code-usage-in-primary-care/2022-23">2022-23</a>
      <a href="{BASE_URL}/2011-12-to-2017-18">multi-year</a>
      <a href="{BASE_URL}/2023-24">duplicate</a>
      <a href="https://example.com/elsewhere">ignore</a>
    </body></html>
    """
    session = DummySession({BASE_URL: DummyResponse(text=html)})
    importer = SnomedUsageImporter()

    periods = importer.get_available_periods(session=session)

    assert periods == [
        "2011-12",
        "2012-13",
        "2013-14",
        "2014-15",
        "2015-16",
        "2016-17",
        "2017-18",
        "2022-23",
        "2023-24",
    ]
    assert session.calls == [(BASE_URL, {"timeout": 30})]


def test_get_page_url_uses_shared_multi_year_page():
    importer = SnomedUsageImporter()
    assert importer.get_page_url("2015-16") == f"{BASE_URL}/2011-12-to-2017-18"
    assert importer.get_page_url("2023-24") == f"{BASE_URL}/2023-24"


def test_find_txt_download_url_returns_matching_file_link():
    period = "2023-24"
    period_url = f"{BASE_URL}/{period}"
    file_url = (
        "https://digital.nhs.uk/binaries/content/assets/website-assets/"
        f"data-and-information/{period}/SNOMED_code_usage_{period}.txt"
    )
    html = f"<html><body><a href='{file_url}'>Download</a></body></html>"
    session = DummySession({period_url: DummyResponse(text=html)})
    importer = SnomedUsageImporter()

    assert importer.find_txt_download_url(period, session=session) == file_url


def test_find_txt_download_url_raises_for_404():
    period = "2099-00"
    period_url = f"{BASE_URL}/{period}"
    session = DummySession({period_url: DummyResponse(status_code=404)})
    importer = SnomedUsageImporter()

    with pytest.raises(requests.HTTPError):
        importer.find_txt_download_url(period, session=session)


def test_find_txt_download_url_raises_on_request_error():
    period = "2023-24"
    period_url = f"{BASE_URL}/{period}"
    session = DummySession(
        {period_url: requests.RequestException("connection problem")}
    )
    importer = SnomedUsageImporter()

    with pytest.raises(requests.RequestException):
        importer.find_txt_download_url(period, session=session)


def test_find_txt_download_url_raises_if_no_link_on_page():
    period = "2023-24"
    period_url = f"{BASE_URL}/{period}"
    html = "<html><body><p>No download links here.</p></body></html>"
    session = DummySession({period_url: DummyResponse(text=html)})
    importer = SnomedUsageImporter()

    with pytest.raises(RuntimeError, match="Could not find .txt download link"):
        importer.find_txt_download_url(period, session=session)


def test_parse_usage_row_parses_star_and_numeric_values():
    assert SnomedUsageImporter._parse_usage_row(
        {"SNOMED_Concept_ID": "123", "Usage": "*"}
    ) == ("123", None)
    assert SnomedUsageImporter._parse_usage_row(
        {"SNOMED_Concept_ID": "456", "Usage": "1,234"}
    ) == ("456", 1234)


def test_parse_usage_row_returns_none_for_blank_id():
    assert (
        SnomedUsageImporter._parse_usage_row({"SNOMED_Concept_ID": "", "Usage": "10"})
        is None
    )


def test_parse_usage_row_raises_for_invalid_usage_value():
    with pytest.raises(ValueError, match="Unrecognised usage value"):
        SnomedUsageImporter._parse_usage_row(
            {"SNOMED_Concept_ID": "123", "Usage": "abc"}
        )


def test_parse_usage_file_yields_cleaned_rows():
    data = b"SNOMED_Concept_ID\tUsage\n111\t10\n222\t*\n\t99\n333\t1,001\n"
    importer = SnomedUsageImporter()

    rows = list(importer.parse_usage_file(io.BytesIO(data)))

    assert rows == [("111", 10), ("222", None), ("333", 1001)]


@pytest.mark.django_db
def test_import_period_skips_if_release_already_exists():
    period = "2023-24"
    CodeUsageRelease.objects.create(
        coding_system=CODING_SYSTEM, period=period, source_url="https://existing"
    )
    importer = SnomedUsageImporter()

    assert (
        importer.import_period(period, "https://download/new.txt", session=None)
        is False
    )
    assert (
        CodeUsageRelease.objects.filter(
            coding_system=CODING_SYSTEM, period=period
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_import_period_creates_release_and_entries():
    period = "2022-23"
    download_url = "https://download/SNOMED_code_usage_2022-23.txt"
    file_bytes = b"SNOMED_Concept_ID\tUsage\n100\t10\n200\t*\n300\t1,500\n"
    session = DummySession({download_url: DummyResponse(content=file_bytes)})
    importer = SnomedUsageImporter()

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


@pytest.mark.django_db
@patch.object(SnomedUsageImporter, "get_available_periods", return_value=[])
def test_command_raises_if_homepage_has_no_period_links(mock_gap):
    with pytest.raises(
        CommandError,
        match="No snomedct usage periods were discovered",
    ):
        call_command("import_usage")


@pytest.mark.django_db
@patch.object(
    SnomedUsageImporter,
    "find_txt_download_url",
    side_effect=RuntimeError("Could not find .txt download link"),
)
@patch.object(SnomedUsageImporter, "get_available_periods", return_value=["2023-24"])
def test_command_raises_if_period_page_has_no_download_link(mock_gap, mock_find):
    with pytest.raises(CommandError, match=r"Usage import completed with 1 failure"):
        call_command("import_usage")
