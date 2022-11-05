import sqlite3
import subprocess

import pytest
from django.apps import apps
from django.core.management import call_command
from django.db import DEFAULT_DB_ALIAS, connections

from codelists.coding_systems import CODING_SYSTEMS
from coding_systems.bnf.models import Concept as BNFConcept
from coding_systems.versioning.models import (
    CodingSystemRelease,
    update_coding_system_database_connections,
)


@pytest.fixture(autouse=True)
def remove_coding_system_releases(settings):
    # Tests in this file assume that we are migrating coding systems for the first time,
    # so we want to start with no CodingSystemRelease objects
    CodingSystemRelease.objects.all().delete()
    yield


@pytest.fixture(autouse=True)
def database_dump_dir(settings, tmp_path):
    settings.DATABASE_DUMP_DIR = tmp_path


@pytest.fixture
def db_on_disk(tmp_path):
    """
    Our main session fixtures load some snomedct, dmd and icd10 data into test
    dbs called "<coding_system>_test_20200101", but for testing the `migrate_coding_system`
    command we need the coding system data to start off in the default db.

    During the test run, the default test db is an in-memory sqlite db, and `sqlite3 <db> .dump`
    doesn't actually dump anything. This fixture writes a single BNF concept (the simplest of the
    coding system models) into a mock test default database in a temporary file on disk so that
    the tests can load from it.
    """
    sql_file = tmp_path / "test.sql"
    db_file = tmp_path / "testdb.sqlite3"

    with sqlite3.connect(connections.databases[DEFAULT_DB_ALIAS]["NAME"]) as conn:
        with open(sql_file, "w") as outfile:
            res = conn.execute(
                "select sql from sqlite_schema where name = 'bnf_concept';"
            )
            build_sql = f"{res.fetchone()[0]};"
            insert_sql = """
            INSERT INTO bnf_concept(code, type, name, parent_id)
            VALUES (\'01\', \'Chapter\', \'Gastro-Intestinal System\', \'null\');
            """
            build_sql += insert_sql
            outfile.write(build_sql)
    with open(sql_file) as infile:
        subprocess.run(["sqlite3", str(db_file)], stdin=infile, check=True)

    yield db_file


def test_migrate_coding_system(coding_systems_tmp_path):
    assert not CodingSystemRelease.objects.exists()
    call_command("migrate_coding_system", coding_systems=["snomedct"])

    assert CodingSystemRelease.objects.count() == 1
    coding_system_release = CodingSystemRelease.objects.first()
    dbpath = (
        coding_systems_tmp_path
        / "snomedct"
        / f"{coding_system_release.db_name}.sqlite3"
    )
    assert dbpath.exists()


def test_migrate_all_coding_systems(coding_systems_tmp_path):
    assert not CodingSystemRelease.objects.exists()
    call_command("migrate_coding_system")

    # no coding systems specified, defaults to trying all
    assert len(CODING_SYSTEMS) == 8
    # only coding systems that are in INSTALLED_APPS are migrated
    assert CodingSystemRelease.objects.count() == 6
    versioned_coding_systems = CodingSystemRelease.objects.values_list(
        "coding_system", flat=True
    )
    non_versioned_coding_systems = set(CODING_SYSTEMS) - set(versioned_coding_systems)
    assert set(apps.app_configs) & non_versioned_coding_systems == set()

    for coding_system_release in CodingSystemRelease.objects.all():
        dbpath = (
            coding_systems_tmp_path
            / coding_system_release.coding_system
            / f"{coding_system_release.db_name}.sqlite3"
        )
        assert dbpath.exists()


def test_migrate_coding_system_rerun(coding_systems_tmp_path):
    assert not CodingSystemRelease.objects.exists()
    call_command("migrate_coding_system", coding_systems=["snomedct"])

    coding_system_release = CodingSystemRelease.objects.first()
    first_import = coding_system_release.import_timestamp

    # try running again, import date unchanged
    call_command("migrate_coding_system", coding_systems=["snomedct"])
    # still just one CodingSystemRelease
    assert CodingSystemRelease.objects.count() == 1
    coding_system_release.refresh_from_db()
    assert coding_system_release.import_timestamp == first_import

    # try running again with force, import date updated
    call_command("migrate_coding_system", coding_systems=["snomedct"], force=True)
    # still just one CodingSystemRelease
    assert CodingSystemRelease.objects.count() == 1
    coding_system_release.refresh_from_db()
    assert coding_system_release.import_timestamp > first_import


def test_migrate_coding_system_loads_data(db_on_disk, coding_systems_tmp_path):
    assert not CodingSystemRelease.objects.exists()
    call_command(
        "migrate_coding_system",
        coding_systems=["bnf"],
        source_db=db_on_disk,
    )
    assert CodingSystemRelease.objects.count() == 1
    coding_system_release = CodingSystemRelease.objects.first()
    dbpath = (
        coding_systems_tmp_path / "bnf" / f"{coding_system_release.db_name}.sqlite3"
    )
    assert dbpath.exists()

    # update the connections so `using` can find the db we've just loaded
    update_coding_system_database_connections()
    assert BNFConcept.objects.using(coding_system_release.db_name).count() == 1
