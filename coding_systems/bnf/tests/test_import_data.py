import csv
import re
from datetime import date
from unittest.mock import patch

import pytest
from django.conf import settings
from django.db import connections

from coding_systems.base.tests.dynamic_db_classes import (
    DynamicDatabaseTestCaseWithTmpPath,
)
from coding_systems.bnf.import_data import import_data
from coding_systems.bnf.models import Concept
from coding_systems.conftest import mock_migrate_coding_system
from coding_systems.versioning.models import CodingSystemRelease, ReleaseState


@pytest.fixture(autouse=True)
def mock_migrate():
    with patch(
        "coding_systems.base.import_data_utils.call_command", mock_migrate_coding_system
    ):
        yield


def mock_migrate_coding_system_with_error(*args, **kwargs):
    """
    Mock the migrate command to create the new database file but then raise an
    exception, so we can confirm that the file gets cleaned
    """
    database = kwargs["database"]
    with connections[database].cursor() as cursor:
        cursor.execute("CREATE TABLE test (col1 VARCHAR)")
    assert (
        settings.CODING_SYSTEMS_DATABASE_DIR / "bnf" / f"{database}.sqlite3"
    ).exists()
    raise Exception("expected exception")


@pytest.fixture
def mock_bnf_data_csv_path(tmp_path):
    """Create a temporary directory containing a mock CSV that includes BNF data in the format available from the NHSBSA ODP API.

    The CSV contains 4 rows and includes 13 concepts:
    1. Header row using the NHSBSA ODP column name format.
    2. 7 new concepts.
    3. 3 new concepts and 4 concepts shared with row 2.

    Returns the path to the directory containing the CSV.
    """
    mock_bnf_import_data = [
        [
            "MONTH_YEAR",
            "BNF_CHAPTER",
            "BNF_CHAPTER_CODE",
            "BNF_SECTION",
            "BNF_SECTION_CODE",
            "BNF_PARAGRAPH",
            "BNF_PARAGRAPH_CODE",
            "BNF_SUBPARAGRAPH",
            "BNF_SUBPARAGRAPH_CODE",
            "BNF_CHEMICAL_SUBSTANCE",
            "BNF_CHEMICAL_SUBSTANCE_CODE",
            "BNF_PRODUCT",
            "BNF_PRODUCT_CODE",
            "BNF_PRESENTATION",
            "BNF_PRESENTATION_CODE",
        ],
        [
            "2025-09",
            "Gastro-Intestinal System",
            "01",
            "Dyspepsia and gastro-oesophageal reflux disease",
            "0101",
            "Antacids and simeticone",
            "010101",
            "Antacids and simeticone",
            "0101010",
            "Other antacid and simeticone preparations",
            "010101000",
            "Proprietary compound preparation BNF 0101010",
            "010101000BB",
            "Indigestion mixture",
            "010101000BBAJA0",
        ],
        [
            "2025-09",
            "Gastro-Intestinal System",
            "01",
            "Dyspepsia and gastro-oesophageal reflux disease",
            "0101",
            "Antacids and simeticone",
            "010101",
            "Antacids and simeticone",
            "0101010",
            "Alexitol sodium",
            "0101010A0",
            "Alexitol sodium",
            "0101010A0AA",
            "Alexitol sodium 360mg tablets",
            "0101010A0AAAAAA",
        ],
    ]
    csv_dir = tmp_path / "data"
    csv_dir.mkdir()
    with open(
        csv_dir / "data.csv",
        "w",
        newline="",
    ) as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows(mock_bnf_import_data)
    return str(csv_dir / "data.csv")


def test_import_data_no_csv_files(tmp_path):
    other_file = tmp_path / "test.txt"
    other_file.touch()

    with pytest.raises(
        ValueError,
        match=re.escape(f"Expected file path str ending '.csv', got '{other_file}'"),
    ):
        import_data(str(other_file), release_name="v1", valid_from=date(2022, 10, 1))


class BNFDynamicDatabaseTestCaseWithTmpPath(DynamicDatabaseTestCaseWithTmpPath):
    # The tests in this module are a distinct case
    # compared with the other coding system tests.
    # When working with test import data,
    # the other tests use fixtures in the respository.
    # These tests instead use a fixture to write out temporary files
    # that will subsequently get imported.

    # Set this fixture as `autouse`:
    # all the tests currently using this class use this import data fixture.
    @pytest.fixture(autouse=True)
    def _set_import_data_from_fixture(self, mock_bnf_data_csv_path):
        self.import_data_path = mock_bnf_data_csv_path


class TestImportData(BNFDynamicDatabaseTestCaseWithTmpPath):
    db_aliases = [
        "bnf_release-1-a_20221001",
    ]
    coding_system_subpath_name = "bnf"

    @pytest.mark.usefixtures("setup_coding_systems")
    def test_import_data(self):
        """Test importing BNF coding system data with dynamic database creation."""
        cs_release_count = CodingSystemRelease.objects.count()

        # Execute import.
        import_data(
            self.import_data_path,
            release_name="release 1 A",
            valid_from=date(2022, 10, 1),
            import_ref="Ref",
        )

        # Verify CodingSystemRelease creation.
        assert CodingSystemRelease.objects.count() == cs_release_count + 1
        cs_release = CodingSystemRelease.objects.latest("id")

        # Verify release details.
        assert cs_release.coding_system == "bnf"
        assert cs_release.release_name == "release 1 A"
        assert cs_release.valid_from == date(2022, 10, 1)
        assert cs_release.import_ref == "Ref"

        # Verify database file creation and configuration.
        assert self.expected_db_path.exists()
        assert cs_release.database_alias in settings.DATABASES

        # Verify imported concepts.
        assert Concept.objects.using("bnf_release-1-a_20221001").count() == 10


class TestImportDataExisting(BNFDynamicDatabaseTestCaseWithTmpPath):
    db_aliases = [
        "bnf_v1-1_20221001",
    ]
    coding_system_subpath_name = "bnf"

    @pytest.mark.usefixtures("setup_coding_systems")
    def test_import_data_existing_coding_system_release(self):
        # Set up an existing CodingSystemRelease and DB file.
        cs_release = CodingSystemRelease.objects.create(
            coding_system="bnf",
            release_name="v1-1",
            valid_from=date(2022, 10, 1),
            import_ref="A first ref",
            state=ReleaseState.READY,
        )
        cs_release_count = CodingSystemRelease.objects.count()
        initial_timestamp = cs_release.import_timestamp
        self.expected_db_path.touch()

        # Execute import.
        import_data(
            self.import_data_path,
            release_name="v1-1",
            valid_from=date(2022, 10, 1),
            import_ref="Ref",
        )

        # CodingSystemRelease has been updated with new import timestamp and ref.
        assert CodingSystemRelease.objects.count() == cs_release_count
        cs_release.refresh_from_db()
        assert cs_release.import_ref == "Ref"
        assert cs_release.import_timestamp > initial_timestamp

        # Verify imported concepts.
        assert Concept.objects.using("bnf_v1-1_20221001").count() == 10

        # Backup file (created from the existing db file during setup) has been removed.
        assert not self.expected_db_path.with_suffix(".bu").exists()


def test_import_error(coding_systems_tmp_path, mock_bnf_data_csv_path):
    cs_release_count = CodingSystemRelease.objects.count()

    # raise an exception after the migrate command; i.e after the setup that
    # creates the CodingSystemRelease and the new db file
    with patch("coding_systems.bnf.import_data.csv.DictReader", side_effect=Exception):
        with pytest.raises(Exception):
            import_data(
                mock_bnf_data_csv_path,
                release_name="release 2",
                valid_from=date(2022, 10, 1),
                import_ref="Ref",
            )

    # new CodingSystemRelease has been removed
    assert CodingSystemRelease.objects.count() == cs_release_count
    # new db path has been removed
    assert not (
        coding_systems_tmp_path / "bnf" / "bnf_release-2_20221001.sqlite3"
    ).exists()


def test_import_setup_error(coding_systems_tmp_path, mock_bnf_data_csv_path):
    cs_release_count = CodingSystemRelease.objects.count()

    # raise an exception during the setup that creates the CodingSystemRelease and the new db file
    with patch(
        "coding_systems.base.import_data_utils.call_command",
        side_effect=Exception("expected exception"),
    ):
        with pytest.raises(Exception, match="expected exception"):
            import_data(
                mock_bnf_data_csv_path,
                release_name="release 3",
                valid_from=date(2022, 10, 1),
                import_ref="Ref",
            )

    # new CodingSystemRelease has been removed
    assert CodingSystemRelease.objects.count() == cs_release_count
    # new db path has been removed
    assert not (
        coding_systems_tmp_path / "bnf" / "bnf_release-3_20221001.sqlite3"
    ).exists()
    # no backup db path has been created
    assert not (
        coding_systems_tmp_path / "bnf" / "bnf_release-3_20221001.sqlite3.bu"
    ).exists()


def test_import_setup_error_existing_release(
    coding_systems_tmp_path, mock_bnf_data_csv_path
):
    # set up an existing CodingSystemRelease and db file
    cs_release = CodingSystemRelease.objects.create(
        coding_system="bnf",
        release_name="v_error_setup",
        valid_from=date(2022, 10, 1),
        import_ref="A first ref",
        state=ReleaseState.READY,
    )
    cs_release_count = CodingSystemRelease.objects.count()
    initial_timestamp = cs_release.import_timestamp
    db_dir = coding_systems_tmp_path / "bnf"
    db_dir.mkdir(parents=True, exist_ok=True)
    db_file = db_dir / "bnf_v_error_setup_20221001.sqlite3"
    db_file.touch()
    assert db_file.exists()

    # raise an exception during the setup that creates the CodingSystemRelease and the new db file
    with patch(
        "coding_systems.base.import_data_utils.call_command",
        side_effect=Exception("expected exception"),
    ):
        with pytest.raises(Exception, match="expected exception"):
            import_data(
                mock_bnf_data_csv_path,
                release_name="v_error_setup",
                valid_from=date(2022, 10, 1),
                import_ref="Ref",
            )

    # CodingSystemRelease still exists
    assert CodingSystemRelease.objects.count() == cs_release_count
    cs_release.refresh_from_db()
    # import timestamp and ref remains the same as before the errored import
    assert cs_release.import_timestamp == initial_timestamp
    assert cs_release.import_ref == "A first ref"

    # new db path still exists
    assert db_file.exists()
    # backup path does not exist
    assert not (db_dir / "bnf_v_error_setup_20221001.sqlite3.bu").exists()


class TestImportMigrationError(BNFDynamicDatabaseTestCaseWithTmpPath):
    db_aliases = [
        "bnf_migrate-error_20221001",
    ]
    coding_system_subpath_name = "bnf"

    def test_import_error_during_migration(self):
        cs_release_count = CodingSystemRelease.objects.count()

        # Raise an exception during migration, expect rollback.
        with patch(
            "coding_systems.base.import_data_utils.call_command",
            mock_migrate_coding_system_with_error,
        ):
            with pytest.raises(Exception, match="expected exception"):
                import_data(
                    self.import_data_path,
                    release_name="migrate error",
                    valid_from=date(2022, 10, 1),
                    import_ref="Ref",
                )

        # New CodingSystemRelease has been removed.
        assert CodingSystemRelease.objects.count() == cs_release_count
        # New db path has been removed.
        assert not self.expected_db_path.exists()
