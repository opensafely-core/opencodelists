from datetime import datetime, timezone

import pytest
from django.db import connections

from codelists.coding_systems import CODING_SYSTEMS
from coding_systems.versioning.models import CodingSystemRelease, ReleaseState


@pytest.fixture
def coding_system_release():
    yield CodingSystemRelease.objects.create(
        coding_system="snomedct",
        release_name="v1",
        import_ref="ref",
        valid_from=datetime(2022, 10, 1, tzinfo=timezone.utc),
        state=ReleaseState.READY,
    )


@pytest.fixture
def coding_systems_tmp_path(settings, tmp_path):
    settings.CODING_SYSTEMS_DATABASE_DIR = tmp_path
    for coding_system in CODING_SYSTEMS:
        (tmp_path / coding_system).mkdir(parents=True, exist_ok=True)
    yield tmp_path


def mock_migrate_coding_system(*args, **kwargs):
    """
    `import_data` runs `migrate` for the coding system app, to set up the the newly
    created coding system version database.  However, tests run with --no-migrations,
    so this function uses the schema from the test database for the relevant coding
    system to set up the new db in tests (note that the default db can't be used
    because the database router prevents migrations on coding system tables for the
    default db)
    """
    database = kwargs["database"]
    coding_system, _ = database.split("_", 1)
    test_db_connections = [
        db for db in connections if db.startswith(coding_system) and db != database
    ]
    assert len(test_db_connections) == 1
    test_db_connection = test_db_connections[0]
    with connections[test_db_connection].cursor() as cursor:
        res = cursor.execute(
            f"select sql from sqlite_schema where name like '{coding_system}_%';"
        )
        table_defs = res.fetchall()
        build_sql = [f"{defn[0]};" for defn in table_defs]

    with connections[database].cursor() as cursor:
        for sql in build_sql:
            cursor.execute(sql)
