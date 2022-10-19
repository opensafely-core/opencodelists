import pytest
from django.apps import apps
from django.core.management import call_command

from codelists.coding_systems import CODING_SYSTEMS
from coding_systems.versioning.models import CodingSystemVersion


@pytest.fixture
def cleanup_db_files(settings):
    yield
    for coding_system_version in CodingSystemVersion.objects.all():
        dbpath = settings.DATABASE_DIR / f"{coding_system_version.db_name}.sqlite3"
        if dbpath.exists():  # pragma: no cover
            dbpath.unlink()


def test_migrate_coding_system(cleanup_db_files, settings, tmp_path):
    settings.DATABASE_DUMP_DIR = tmp_path

    assert not CodingSystemVersion.objects.exists()
    call_command("migrate_coding_system", coding_systems=["snomedct"])

    assert CodingSystemVersion.objects.count() == 1
    coding_system_ver = CodingSystemVersion.objects.first()
    dbpath = settings.DATABASE_DIR / f"{coding_system_ver.db_name}.sqlite3"
    assert dbpath.exists()


def test_migrate_all_coding_systems(cleanup_db_files, settings, tmp_path):
    settings.DATABASE_DUMP_DIR = tmp_path

    assert not CodingSystemVersion.objects.exists()
    call_command("migrate_coding_system")

    # no coding systems specified, defaults to trying all
    assert len(CODING_SYSTEMS) == 8
    # only coding systems that are in INSTALLED_APPS are migrated
    assert CodingSystemVersion.objects.count() == 6
    versioned_coding_systems = CodingSystemVersion.objects.values_list(
        "coding_system", flat=True
    )
    non_versioned_coding_systems = set(CODING_SYSTEMS) - set(versioned_coding_systems)
    assert set(apps.app_configs) & non_versioned_coding_systems == set()

    for coding_system_version in CodingSystemVersion.objects.all():
        dbpath = settings.DATABASE_DIR / f"{coding_system_version.db_name}.sqlite3"
        assert dbpath.exists()


def test_migrate_coding_system_rerun(cleanup_db_files, settings, tmp_path):
    settings.DATABASE_DUMP_DIR = tmp_path

    assert not CodingSystemVersion.objects.exists()
    call_command("migrate_coding_system", coding_systems=["snomedct"])

    coding_system_ver = CodingSystemVersion.objects.first()
    first_import = coding_system_ver.import_timestamp

    # try running again, import date unchanged
    call_command("migrate_coding_system", coding_systems=["snomedct"])
    # still just one CodingSystemVersion
    assert CodingSystemVersion.objects.count() == 1
    coding_system_ver.refresh_from_db()
    assert coding_system_ver.import_timestamp == first_import

    # try running again with force, import date updated
    call_command("migrate_coding_system", coding_systems=["snomedct"], force=True)
    # still just one CodingSystemVersion
    assert CodingSystemVersion.objects.count() == 1
    coding_system_ver.refresh_from_db()
    assert coding_system_ver.import_timestamp > first_import
