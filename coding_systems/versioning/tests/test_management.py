import sqlite3
import subprocess

import pytest
from django.apps import apps
from django.core.management import call_command
from django.db import DEFAULT_DB_ALIAS, connections

from codelists.coding_systems import CODING_SYSTEMS
from coding_systems.snomedct.models import Concept
from coding_systems.versioning.models import (
    CodingSystemVersion,
    update_coding_system_database_connections,
)


@pytest.fixture(autouse=True)
def cleanup_db_files(settings):
    yield
    for coding_system_version in CodingSystemVersion.objects.all():
        dbpath = (
            settings.CODING_SYSTEMS_DATABASE_DIR
            / coding_system_version.coding_system
            / f"{coding_system_version.db_name}.sqlite3"
        )
        if dbpath.exists():  # pragma: no cover
            dbpath.unlink()


@pytest.fixture
def db_on_disk(tmp_path):
    """
    During the test run, the default db is an in-memory sqlite db, and `sqlite3 <db> .dump`
    doesn't actually dump anything. This writes the snomed tables from the test db to a
    temporary file on disk.
    """
    sql_file = tmp_path / "test.sql"
    db_file = tmp_path / "testdb.sqlite3"
    with sqlite3.connect(connections.databases[DEFAULT_DB_ALIAS]["NAME"]) as conn:
        with open(sql_file, "w") as outfile:
            res = conn.execute(
                "select sql from sqlite_schema where name like 'snomedct_%';"
            )
            table_defs = res.fetchall()
            build_sql = "\n".join([f"{defn[0]};" for defn in table_defs])
            for model in apps.get_app_config("snomedct").get_models():
                table_name = model._meta.db_table
                cols = ", ".join(f.attname for f in model._meta.fields)
                params = ", ".join("?" for f in model._meta.fields)
                select_sql = f"SELECT * FROM '{table_name}';"
                value_rows = conn.execute(select_sql)
                for params in value_rows:
                    insert_sql = f"\nINSERT INTO {table_name}({cols}) VALUES {params};"
                    build_sql += insert_sql
            outfile.write(build_sql)

    with open(sql_file) as infile:
        subprocess.run(["sqlite3", str(db_file)], stdin=infile, check=True)

    yield db_file


def test_migrate_coding_system(settings, tmp_path):
    settings.DATABASE_DIR = tmp_path

    assert not CodingSystemVersion.objects.exists()
    call_command("migrate_coding_system", coding_systems=["snomedct"])

    assert CodingSystemVersion.objects.count() == 1
    coding_system_ver = CodingSystemVersion.objects.first()
    dbpath = (
        settings.CODING_SYSTEMS_DATABASE_DIR
        / "snomedct"
        / f"{coding_system_ver.db_name}.sqlite3"
    )
    assert dbpath.exists()


def test_migrate_all_coding_systems(settings, tmp_path):
    settings.DATABASE_DIR = tmp_path

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
        dbpath = (
            settings.CODING_SYSTEMS_DATABASE_DIR
            / coding_system_version.coding_system
            / f"{coding_system_version.db_name}.sqlite3"
        )
        assert dbpath.exists()


def test_migrate_coding_system_rerun(settings, tmp_path):
    settings.DATABASE_DIR = tmp_path

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


def test_migrate_coding_system_loads_data(
    db_on_disk, snomedct_data, settings, tmp_path
):
    settings.DATABASE_DIR = tmp_path
    assert not CodingSystemVersion.objects.exists()
    call_command(
        "migrate_coding_system", coding_systems=["snomedct"], source_db=db_on_disk
    )
    assert CodingSystemVersion.objects.count() == 1
    coding_system_ver = CodingSystemVersion.objects.first()
    dbpath = (
        settings.CODING_SYSTEMS_DATABASE_DIR
        / "snomedct"
        / f"{coding_system_ver.db_name}.sqlite3"
    )
    assert dbpath.exists()

    # update the connections so `using` can find the db we've just loaded
    update_coding_system_database_connections()
    assert (
        Concept.objects.count()
        == Concept.objects.using(coding_system_ver.db_name).count()
        > 0
    )
