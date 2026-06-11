import json
import zipfile
from datetime import date
from types import SimpleNamespace

import pytest

from coding_systems.icd10 import release_metadata


def _write_zip(path, members):
    with zipfile.ZipFile(path, "w") as zf:
        for filename, content in members.items():
            zf.writestr(filename, content)


def test_xml_file_info_returns_single_xml_member(tmp_path):
    zip_path = tmp_path / "release.zip"
    _write_zip(zip_path, {"icd.xml": "xml", "README.txt": "text"})

    info = release_metadata.xml_file_info(zip_path)

    assert info.filename == "icd.xml"
    assert info.file_size == 3


@pytest.mark.parametrize(
    "members",
    [
        {"README.txt": "text"},
        {"one.xml": "xml", "two.xml": "xml"},
    ],
)
def test_xml_file_info_fails_unless_zip_contains_exactly_one_xml(tmp_path, members):
    zip_path = tmp_path / "release.zip"
    _write_zip(zip_path, members)

    with pytest.raises(ValueError, match="Expected exactly one XML file"):
        release_metadata.xml_file_info(zip_path)


def test_release_record_uses_forced_download_and_zip_member_metadata(
    tmp_path, monkeypatch
):
    zip_path = tmp_path / "release.zip"
    fixed_date_time = (2023, 4, 5, 12, 0, 0)

    def fake_download_zip(release_dir, year, force_download):
        assert release_dir == tmp_path
        assert year == "2016"
        assert force_download is True
        return zip_path

    monkeypatch.setattr(
        "coding_systems.icd10.release_metadata.download_zip",
        fake_download_zip,
    )
    monkeypatch.setattr(
        "coding_systems.icd10.release_metadata.xml_file_info",
        lambda path: SimpleNamespace(
            filename="icd102016en.xml",
            date_time=fixed_date_time,
            file_size=123,
        ),
    )

    assert release_metadata.release_record(tmp_path, "2016") == {
        "url": "https://icdcdn.who.int/icd10/claml/icd102016en.xml.zip",
        "zip_filename": "icd102016en.xml.zip",
        "xml_filename": "icd102016en.xml",
        "xml_last_updated": date(2023, 4, 5).isoformat(),
        "xml_file_size": 123,
    }


def test_build_record_returns_records_for_both_release_years(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "coding_systems.icd10.release_metadata.release_record",
        lambda release_dir, year: {"year": year},
    )

    assert release_metadata.build_record(tmp_path) == {
        "source": "https://icdcdn.who.int/icd10/index.html",
        "releases": {"2016": {"year": "2016"}, "2019": {"year": "2019"}},
    }


def test_check_claml_zip_metadata_returns_without_writing_when_record_is_unchanged(
    tmp_path, monkeypatch, capsys
):
    record_path = tmp_path / "claml_metadata.json"
    record = {"source": "source", "releases": {}}
    record_path.write_text(json.dumps(record))

    monkeypatch.setattr(
        "coding_systems.icd10.release_metadata.build_record",
        lambda release_dir: record,
    )

    release_metadata.check_claml_zip_metadata(tmp_path, record_path)

    assert "no changes" in capsys.readouterr().out
    assert json.loads(record_path.read_text()) == record


def test_check_claml_zip_metadata_writes_changed_record(tmp_path, monkeypatch, capsys):
    record_path = tmp_path / "claml_metadata.json"
    record_path.write_text(json.dumps({"source": "old"}))
    record = {"source": "new", "releases": {}}

    monkeypatch.setattr(
        "coding_systems.icd10.release_metadata.build_record",
        lambda release_dir: record,
    )

    release_metadata.check_claml_zip_metadata(tmp_path, record_path)

    assert "CHANGE DETECTED" in capsys.readouterr().out
    assert json.loads(record_path.read_text()) == record


def test_no_output_on_first_run(tmp_path, capsys):
    record_path = tmp_path / "claml_metadata.json"

    # Simulate first run with no existing record
    release_metadata.check_claml_zip_metadata(tmp_path, record_path)

    assert capsys.readouterr().out == ""
    assert record_path.exists()
