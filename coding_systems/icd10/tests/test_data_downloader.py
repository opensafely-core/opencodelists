import zipfile

import pytest

from coding_systems.icd10.data_downloader import (
    download_release,
    download_zip,
    extract_xml_from_zip,
    get_release_metadata,
)


def test_get_release_metadata_rejects_unsupported_year():
    with pytest.raises(ValueError, match="Unsupported year: 2020"):
        get_release_metadata("2020")


def test_download_zip_uses_cached_zip_without_network(tmp_path, monkeypatch):
    zip_path = tmp_path / "icd102016en.xml.zip"
    zip_path.write_bytes(b"cached")

    def fail_urlretrieve(url, path):
        raise AssertionError("urlretrieve should not be called")

    monkeypatch.setattr(
        "coding_systems.icd10.data_downloader.urllib.request.urlretrieve",
        fail_urlretrieve,
    )

    assert download_zip(tmp_path, "2016") == zip_path
    assert zip_path.read_bytes() == b"cached"


def test_download_zip_downloads_missing_zip_with_expected_url(tmp_path, monkeypatch):
    calls = []

    def fake_urlretrieve(url, path):
        calls.append((url, path))
        path.write_bytes(b"downloaded")

    monkeypatch.setattr(
        "coding_systems.icd10.data_downloader.urllib.request.urlretrieve",
        fake_urlretrieve,
    )

    zip_path = download_zip(tmp_path, "2019")

    assert zip_path == tmp_path / "icd102019en.xml.zip"
    assert zip_path.read_bytes() == b"downloaded"
    assert calls == [
        (
            "https://icdcdn.who.int/icd10/claml/icd102019en.xml.zip",
            tmp_path / "icd102019en.xml.zip",
        )
    ]


def test_download_zip_downloads_when_forced_even_if_zip_exists(tmp_path, monkeypatch):
    zip_path = tmp_path / "icd102016en.xml.zip"
    zip_path.write_bytes(b"stale")

    def fake_urlretrieve(url, path):
        path.write_bytes(b"fresh")

    monkeypatch.setattr(
        "coding_systems.icd10.data_downloader.urllib.request.urlretrieve",
        fake_urlretrieve,
    )

    assert download_zip(tmp_path, "2016", force_download=True) == zip_path
    assert zip_path.read_bytes() == b"fresh"


def test_extract_xml_from_zip_uses_cached_xml_without_reextracting(tmp_path):
    zip_path = tmp_path / "icd102016en.xml.zip"
    xml_path = tmp_path / "icd102016en.xml"
    xml_path.write_text("cached")
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("icd102016en.xml", "fresh")

    assert extract_xml_from_zip(zip_path, "2016") == xml_path
    assert xml_path.read_text() == "cached"


def test_extract_xml_from_zip_extracts_missing_xml_without_force(tmp_path):
    zip_path = tmp_path / "icd102016en.xml.zip"
    xml_path = tmp_path / "icd102016en.xml"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("icd102016en.xml", "fresh")

    assert extract_xml_from_zip(zip_path, "2016") == xml_path
    assert xml_path.read_text() == "fresh"


def test_extract_xml_from_zip_extracts_when_forced(tmp_path):
    zip_path = tmp_path / "icd102016en.xml.zip"
    xml_path = tmp_path / "icd102016en.xml"
    xml_path.write_text("stale")
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("icd102016en.xml", "fresh")

    assert extract_xml_from_zip(zip_path, "2016", force_download=True) == xml_path
    assert xml_path.read_text() == "fresh"


def test_download_release_downloads_zip_then_extracts_xml(monkeypatch):
    calls = []

    def fake_download_zip(release_dir, year, force_download):
        calls.append(("download_zip", release_dir, year, force_download))
        return "/tmp/icd10.zip"

    def fake_extract_xml_from_zip(zip_path, year, force_download):
        calls.append(("extract_xml_from_zip", zip_path, year, force_download))
        return "/tmp/icd10.xml"

    monkeypatch.setattr(
        "coding_systems.icd10.data_downloader.download_zip",
        fake_download_zip,
    )
    monkeypatch.setattr(
        "coding_systems.icd10.data_downloader.extract_xml_from_zip",
        fake_extract_xml_from_zip,
    )

    assert (
        download_release("/tmp/cache", "2019", force_download=True) == "/tmp/icd10.xml"
    )
    assert calls == [
        ("download_zip", "/tmp/cache", "2019", True),
        ("extract_xml_from_zip", "/tmp/icd10.zip", "2019", True),
    ]
