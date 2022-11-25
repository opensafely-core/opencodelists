from datetime import datetime

import pytest
from django.db import DEFAULT_DB_ALIAS, connections

from coding_systems.base.import_data_utils import update_codelist_version_compatibility
from coding_systems.bnf.models import Concept
from coding_systems.conftest import mock_migrate_coding_system
from coding_systems.versioning.models import CodingSystemRelease, ReleaseState


@pytest.fixture
def bnf_csr():
    yield CodingSystemRelease.objects.create(
        coding_system="bnf",
        release_name="import-data",
        valid_from=datetime(2022, 11, 1),
        state=ReleaseState.READY,
    )


def setup_db(csr, exclude_last_concept=False):
    # At this point, the test databases have been configured as in-memory sqlite dbs
    # we copy the default db config and update the name (which in tests is something
    # like "file:memorydb_default?mode=memory&cache=shared" rather than a path to a
    # sqlite file on disk) to the expected release db name
    db_name = connections.databases[DEFAULT_DB_ALIAS]["NAME"].replace(
        "default", csr.database_alias
    )
    connections.databases[csr.database_alias] = {
        **connections.databases[DEFAULT_DB_ALIAS],
        "NAME": db_name,
    }
    mock_migrate_coding_system(database=csr.database_alias)
    concepts = Concept.objects.using("bnf_test_20200101").all()
    if exclude_last_concept:
        concepts = list(concepts)[:-1]
    for concept in concepts:
        Concept.objects.using(csr.database_alias).create(
            code=concept.code,
            type=concept.type,
            name=concept.name,
            parent=concept.parent,
        )


def cleanup_db(csr):
    # The in-memory db doesn't get automatically removed, so manually drop the
    # tables for the next test
    with connections[csr.database_alias].cursor() as cursor:
        cursor.execute("DROP TABLE bnf_concept")


@pytest.fixture
def bnf_release(bnf_csr):
    # setup the database as a duplicate of the fixture one
    setup_db(bnf_csr)
    yield bnf_csr
    cleanup_db(bnf_csr)


@pytest.fixture
def bnf_release_excl_last_concept(bnf_csr):
    # setup the database as a duplicate of the fixture one, omitting the last concept
    setup_db(bnf_csr, exclude_last_concept=True)
    yield bnf_csr
    cleanup_db(bnf_csr)


def test_update_codelist_version_compatibility_no_searches(
    bnf_version_asthma, coding_systems_tmp_path, bnf_release
):
    update_codelist_version_compatibility("bnf", bnf_release.database_alias)
    # this version has no searches, so can't be confirmed as compatible
    assert not bnf_version_asthma.compatible_releases.exists()


def test_update_codelist_version_compatibility_with_search(
    bnf_version_with_search, coding_systems_tmp_path, bnf_release
):
    update_codelist_version_compatibility("bnf", bnf_release.database_alias)
    # this version has a search, and the new release will return the same results,
    # so it is compatible
    assert bnf_version_with_search.compatible_releases.first() == bnf_release


def test_update_codelist_version_compatibility_with_mismatched_search(
    bnf_version_with_search, coding_systems_tmp_path, bnf_release_excl_last_concept
):
    # setup the db, but omit the last Concept from the existing db, so the search
    # will return different results
    update_codelist_version_compatibility(
        "bnf", bnf_release_excl_last_concept.database_alias
    )
    # this version has a search, but the new release returns different results,
    # so it is not compatible
    assert not bnf_version_with_search.compatible_releases.exists()
