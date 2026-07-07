import zipfile

import pytest

from coding_systems.icd10.data_downloader import (
    Downloader,
    Year,
)
from coding_systems.versioning.models import CodingSystemRelease


EMPTY_FILES_COMBINED_DIGEST = "ac9c542684f271e7215c00369bbb793e"


def test_get_release_metadata_rejects_unsupported_year(tmp_path):
    downloader = Downloader(tmp_path)
    with pytest.raises(ValueError, match="'2020' is not a valid Year"):
        downloader.get_release_metadata(Year("2020"))


def test_download_zip_uses_cached_zip_without_network(tmp_path, monkeypatch):
    zip_path = tmp_path / "icd102016en.xml.zip"
    zip_path.write_bytes(b"cached")
    downloader = Downloader(tmp_path)

    def fail_urlretrieve(url, path):
        raise AssertionError("urlretrieve should not be called")

    monkeypatch.setattr(
        "coding_systems.icd10.data_downloader.urllib.request.urlretrieve",
        fail_urlretrieve,
    )

    assert downloader.download_zip(Year("2016")) == zip_path
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
    downloader = Downloader(tmp_path)

    zip_path = downloader.download_zip(Year("2019"))

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

    downloader = Downloader(tmp_path)
    assert downloader.download_zip(Year("2016"), force_download=True) == zip_path
    assert zip_path.read_bytes() == b"fresh"


def test_extract_xml_from_zip_uses_cached_xml_without_reextracting(tmp_path):
    zip_path = tmp_path / "icd102016en.xml.zip"
    xml_path = tmp_path / "icd102016en.xml"
    xml_path.write_text("cached")
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("icd102016en.xml", "fresh")

    downloader = Downloader(tmp_path)
    assert downloader.extract_xml_from_zip(zip_path, Year("2016")) == xml_path
    assert xml_path.read_text() == "cached"


def test_extract_xml_from_zip_extracts_missing_xml_without_force(tmp_path):
    zip_path = tmp_path / "icd102016en.xml.zip"
    xml_path = tmp_path / "icd102016en.xml"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("icd102016en.xml", "fresh")

    downloader = Downloader(tmp_path)
    assert downloader.extract_xml_from_zip(zip_path, Year("2016")) == xml_path
    assert xml_path.read_text() == "fresh"


def test_extract_xml_from_zip_extracts_when_forced(tmp_path):
    zip_path = tmp_path / "icd102016en.xml.zip"
    xml_path = tmp_path / "icd102016en.xml"
    xml_path.write_text("stale")
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("icd102016en.xml", "fresh")

    downloader = Downloader(tmp_path)
    assert (
        downloader.extract_xml_from_zip(zip_path, Year("2016"), force_extract=True)
        == xml_path
    )
    assert xml_path.read_text() == "fresh"


def test_download_release_downloads_zip_then_extracts_xml(monkeypatch):
    calls = []

    def fake_download_zip(self, year, force_download):
        calls.append(("download_zip", year.value, force_download))
        return "/tmp/icd10.zip"

    def fake_extract_xml_from_zip(self, zip_path, year, force_download):
        calls.append(("extract_xml_from_zip", zip_path, year.value, force_download))
        return "/tmp/icd10.xml"

    monkeypatch.setattr(
        "coding_systems.icd10.data_downloader.Downloader.download_zip",
        fake_download_zip,
    )
    monkeypatch.setattr(
        "coding_systems.icd10.data_downloader.Downloader.extract_xml_from_zip",
        fake_extract_xml_from_zip,
    )

    downloader = Downloader("/tmp/cache")

    assert (
        downloader.download_release(Year("2019"), force_download=True)
        == "/tmp/icd10.xml"
    )
    assert calls == [
        ("download_zip", "2019", True),
        ("extract_xml_from_zip", "/tmp/icd10.zip", "2019", True),
    ]


def test_download_latest_release(monkeypatch, tmp_path):
    downloader = Downloader(tmp_path)

    def fake_download_release(self, year, force_download=False):
        xml_filename = downloader.get_release_metadata(year)["xml_filename"]
        xml_path = tmp_path / xml_filename
        xml_path.touch()
        return xml_path

    monkeypatch.setattr(
        "coding_systems.icd10.data_downloader.Downloader.download_release",
        fake_download_release,
    )
    combined_zip_path, metadata = downloader.download_latest_release()
    assert combined_zip_path == tmp_path / f"combined_{downloader.timestamp}.zip"
    assert metadata == {
        "release_name": f"combined_{downloader.timestamp}_{EMPTY_FILES_COMBINED_DIGEST}",
        "filename": f"combined_{downloader.timestamp}.zip",
        "valid_from": downloader.valid_from,
        "file_metadata": {
            "WHO_2016": downloader.get_release_metadata(Year.WHO_2016),
            "WHO_2019": downloader.get_release_metadata(Year.WHO_2019),
            "NHS_2016": downloader.get_release_metadata(Year.NHS_2016),
        },
    }
    with open(combined_zip_path, "rb") as f:
        with zipfile.ZipFile(f) as zf:
            assert set(zf.namelist()) == {
                downloader.get_release_metadata(Year.WHO_2016)["xml_filename"],
                downloader.get_release_metadata(Year.WHO_2019)["xml_filename"],
                downloader.get_release_metadata(Year.NHS_2016)["xml_filename"],
            }


def test_get_latest_release_with_existing_identical(monkeypatch, tmp_path):
    downloader = Downloader(tmp_path)

    def fake_download_release(self, year, force_download=False):
        xml_filename = downloader.get_release_metadata(year)["xml_filename"]
        xml_path = tmp_path / xml_filename
        xml_path.touch()
        return xml_path

    monkeypatch.setattr(
        "coding_systems.icd10.data_downloader.Downloader.download_release",
        fake_download_release,
    )

    _, metadata = downloader.download_latest_release()

    CodingSystemRelease.objects.create(
        coding_system="icd10",
        release_name=metadata["release_name"],
        valid_from=metadata["valid_from"],
        import_ref="test",
        database_alias=f"icd10_{metadata['release_name']}_{metadata['valid_from'].strftime('%Y%m%d')}",
        state="importing",
    )

    with pytest.raises(ValueError, match="Latest release already exists"):
        downloader.download_latest_release()


def test_get_latest_release_with_existing_different(monkeypatch, tmp_path):
    downloader = Downloader(tmp_path)

    def fake_download_release(self, year, force_download=False):
        xml_filename = downloader.get_release_metadata(year)["xml_filename"]
        xml_path = tmp_path / xml_filename
        xml_path.touch()
        return xml_path

    monkeypatch.setattr(
        "coding_systems.icd10.data_downloader.Downloader.download_release",
        fake_download_release,
    )

    _, metadata = downloader.download_latest_release()

    CodingSystemRelease.objects.create(
        coding_system="icd10",
        release_name=metadata["release_name"],
        valid_from=metadata["valid_from"],
        import_ref="test",
        database_alias=f"icd10_{metadata['release_name']}_{metadata['valid_from'].strftime('%Y%m%d')}",
        state="importing",
    )

    def fake_download_release_new(self, year, force_download=False):
        xml_filename = downloader.get_release_metadata(year)["xml_filename"]
        xml_path = tmp_path / xml_filename
        xml_path.write_text("new content")
        return xml_path

    monkeypatch.setattr(
        "coding_systems.icd10.data_downloader.Downloader.download_release",
        fake_download_release_new,
    )

    _, metadata = downloader.download_latest_release()

    assert not metadata["release_name"].endswith(EMPTY_FILES_COMBINED_DIGEST)
