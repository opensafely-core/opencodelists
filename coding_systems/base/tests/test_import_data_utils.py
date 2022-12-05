from datetime import datetime

import pytest
from django.db import DEFAULT_DB_ALIAS, connections

from builder.actions import create_search
from codelists.coding_systems import CODING_SYSTEMS
from codelists.hierarchy import Hierarchy
from codelists.models import Status
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


@pytest.fixture
def bnf_review_version_with_search(bnf_version_with_search):
    bnf_version_with_search.status = Status.UNDER_REVIEW
    bnf_version_with_search.save()
    yield bnf_version_with_search


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
    # Draft versions are not checked for compatibility; this version is under review
    assert bnf_version_asthma.status == Status.PUBLISHED
    update_codelist_version_compatibility("bnf", bnf_release.database_alias)
    # this version has no searches, but its hierarchy is identical
    assert bnf_version_asthma.compatible_releases.exists()


def test_update_codelist_draft_version_excluded(
    bnf_version_with_search, coding_systems_tmp_path, bnf_release
):
    assert bnf_version_with_search.status == Status.DRAFT
    update_codelist_version_compatibility("bnf", bnf_release.database_alias)
    # this version has an identical hierarchy, and its search will return the same
    # results with the new release, so it is compatible
    assert not bnf_version_with_search.compatible_releases.exists()


def test_update_codelist_version_with_search(
    bnf_review_version_with_search, coding_systems_tmp_path, bnf_release
):
    assert bnf_review_version_with_search.status == Status.UNDER_REVIEW
    update_codelist_version_compatibility("bnf", bnf_release.database_alias)
    # this version has an identical hierarchy, and its search will return the same
    # results with the new release, so it is compatible
    assert bnf_review_version_with_search.compatible_releases.first() == bnf_release


def test_update_codelist_version_compatibility_with_mismatched_search(
    bnf_review_version_with_search,
    coding_systems_tmp_path,
    bnf_release_excl_last_concept,
):
    # setup the db, but omit the last Concept from the existing db, so the search
    # will return different results
    update_codelist_version_compatibility(
        "bnf", bnf_release_excl_last_concept.database_alias
    )
    # this version has a search, but the new release returns different results,
    # so it is not compatible
    assert not bnf_review_version_with_search.compatible_releases.exists()


def test_update_codelist_version_compatibility_with_search_but_mismatched_hierarchy(
    bnf_review_version_with_search,
    coding_systems_tmp_path,
    bnf_release_excl_last_concept,
):
    # setup the db, but omit the last Concept from the existing db
    # Modify the search so that it returns just one code; the hierarchy will differ but
    # search results will remain the same
    bnf_review_version_with_search.searches.all().delete()
    create_search(
        draft=bnf_review_version_with_search,
        code="0301012A0AAABAB",
        codes=["0301012A0AAABAB"],
    )

    existing_hierarchy = bnf_review_version_with_search.hierarchy
    hierarchy_with_new_release = Hierarchy.from_codes(
        coding_system=CODING_SYSTEMS["bnf"](
            database_alias=bnf_release_excl_last_concept.database_alias
        ),
        codes=["0301012A0AAABAB"],
    )
    assert existing_hierarchy.nodes != hierarchy_with_new_release.nodes

    update_codelist_version_compatibility(
        "bnf", bnf_release_excl_last_concept.database_alias
    )
    # this version has a search that returns identical results in the new release
    # but the hierarchies differ, so it is not compatible
    assert not bnf_review_version_with_search.compatible_releases.exists()
