from datetime import UTC, datetime

import pytest
from django.apps import apps
from django.db import DEFAULT_DB_ALIAS, OperationalError, connections

from codelists.coding_systems import CODING_SYSTEMS
from coding_systems.base.tests.dynamic_db_classes import (
    DynamicDatabaseTestCaseWithTmpPath,
)
from coding_systems.conftest import mock_migrate_coding_system
from coding_systems.ctv3.models import TPPConcept, TPPRelationship
from coding_systems.versioning.models import (
    CodingSystemRelease,
    ReleaseState,
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


class TestMismatchedCodingSystemDatabaseRelations(DynamicDatabaseTestCaseWithTmpPath):
    db_alias = "ctv3_testv2_20221101"
    coding_system_subpath_name = "ctv3"

    def test_mismatched_coding_system_database_relations(self):
        # Relations are only allowed if the database matches
        # (Note Mapping instances are an exception; see db_utils.CodingSystemReleaseRouter)

        # make another ctv3 db connection
        CodingSystemRelease.objects.create(
            coding_system="ctv3",
            release_name="testv2",
            valid_from=datetime(2022, 11, 1, tzinfo=UTC),
            state=ReleaseState.READY,
        )
        update_coding_system_database_connections()
        mock_migrate_coding_system(database="ctv3_testv2_20221101")

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


def test_coding_system_routing_with_mismatched_coding_system_db():
    # Migrations on coding system models are only allowed for matching
    # databases.  This means that typically, an attempt to use the wrong coding
    # system database will result in an OperationalError as the tables haven't
    # been created yet.
    # In case tables have been created, (theoretically possible if manually created, or
    # if migrations were run prior to the database router application) the database router
    # also rejects `using` args with a coding system that doesn't match the app.

    # setup: create ctv3 tables in the bnf database
    with connections["ctv3_test_20200101"].cursor() as cursor:
        res = cursor.execute("select sql from sqlite_schema where name like 'ctv3_%';")
        table_defs = res.fetchall()
        build_sql = [f"{defn[0]};" for defn in table_defs]

    with connections["bnf_test_20200101"].cursor() as cursor:
        for sql in build_sql:
            cursor.execute(sql)

    # we can create TPPConcept objects in the bnf database now (note: in reality, migrations
    # should never have run, so this would result in an OperationalError)
    concept1 = TPPConcept.objects.using("bnf_test_20200101").create(
        read_code="1234", description="test1"
    )
    concept2 = TPPConcept.objects.using("bnf_test_20200101").create(
        read_code="5678", description="test2"
    )
    # Attemting to create a TPPRelationship involves foreign keys, so uses
    # the router and rejects the write attempt
    with pytest.raises(
        ValueError, match='"ctv3" models must select a valid version database'
    ):
        TPPRelationship.objects.using("bnf_test_20200101").create(
            ancestor=concept1, descendant=concept2, distance=1
        )
