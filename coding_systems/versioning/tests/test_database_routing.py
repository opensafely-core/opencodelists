from datetime import datetime, timezone

import pytest
from django.apps import apps
from django.db import DEFAULT_DB_ALIAS, OperationalError, connections

from codelists.coding_systems import CODING_SYSTEMS
from coding_systems.ctv3.models import TPPConcept, TPPRelationship
from coding_systems.versioning.models import (
    CodingSystemRelease,
    update_coding_system_database_connections,
)


@pytest.mark.parametrize(
    "coding_system", [cs for cs in CODING_SYSTEMS if cs in apps.app_configs]
)
def test_coding_system_routing_errors_if_no_using_db_specified(coding_system):
    for model_cls in apps.app_configs[coding_system].get_models():
        with pytest.raises(
            ValueError,
            match=f'"{coding_system}" models must be accessed with a `using` argument.',
        ):
            model_cls.objects.filter(pk=1).first()


def setup_ctv3_db():
    """Ensure the ctv3 tables are created in a second test db"""
    CodingSystemRelease.objects.create(
        coding_system="ctv3",
        release_name="testv2",
        valid_from=datetime(2022, 11, 1, tzinfo=timezone.utc),
    )
    update_coding_system_database_connections()

    with connections["ctv3_test_20200101"].cursor() as cursor:
        res = cursor.execute("select sql from sqlite_schema where name LIKE 'ctv3_%';")
        build_sql = [f"{table_defn[0]};" for table_defn in res.fetchall()]
    with connections["ctv3_testv2_20221101"].cursor() as cursor:
        for sql in build_sql:
            cursor.execute(sql)


def test_mismatched_coding_system_database_relations(coding_systems_tmp_path):
    # Relations are only allowed if the database matches
    # (Note Mapping instances are an exception; see db_utils.CodingSystemVersionRouter)

    # make another ctv3 db connection
    setup_ctv3_db()

    ancestor = TPPConcept.objects.using("ctv3_test_20200101").create(
        read_code="11111", description="11111"
    )
    descendant = TPPConcept.objects.using("ctv3_testv2_20221101").create(
        read_code="22222", description="22222"
    )
    # `using` bypasses the router for the creation of the concepts, so it only
    # raises an error when the relationship is created
    with pytest.raises(
        ValueError, match="the current database router prevents this relation"
    ):
        TPPRelationship.objects.using("ctv3_test_20200101").create(
            ancestor=ancestor,
            descendant=descendant,
            distance="1",
        )


def test_coding_systems_migrate_not_allowed_on_default_db():
    # The database router prevents migration of coding system tables on
    # the default database.
    for app in apps.app_configs:
        for model_cls in apps.app_configs[app].get_models():
            if app in CODING_SYSTEMS:
                # Coding system apps are not allowed to migrate on the default database, and raise
                # an OperationError as the tables haven't been created.
                with pytest.raises(
                    OperationalError, match=f"no such table: {model_cls._meta.db_table}"
                ):
                    model_cls.objects.using(DEFAULT_DB_ALIAS).count()
            else:
                # All other apps can be migrated and accessed with the default database
                model_cls.objects.using(DEFAULT_DB_ALIAS).count()


@pytest.mark.parametrize(
    "coding_system,database",
    [
        ("snomedct", "ctv3_test_20200101"),
        ("ctv3", "snomedct_test_20200101"),
    ],
)
def test_coding_systems_migrate_only_allowed_on_coding_system_db(
    coding_system, database
):
    # Migrations on coding system models are only allowed for matching
    # databases (i.e. aliases that start with the coding system id)
    # Attempts to access them using a different coding system's database (i.e.
    # accessing snomedct tables with a ctv3 database and vice versa) raise an
    # OperationalErrors as the tables haven't been created.
    for model_cls in apps.app_configs[coding_system].get_models():
        with pytest.raises(
            OperationalError, match=f"no such table: {model_cls._meta.db_table}"
        ):
            model_cls.objects.using(database).filter(pk=1).first()
