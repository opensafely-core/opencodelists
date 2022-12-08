from datetime import datetime

import pytest
from django.db import DEFAULT_DB_ALIAS, connections

from builder.actions import create_search
from builder.actions import save as save_draft_for_review
from codelists.coding_systems import CODING_SYSTEMS
from codelists.hierarchy import Hierarchy
from codelists.models import Status
from coding_systems.base.import_data_utils import update_codelist_version_compatibility
from coding_systems.bnf.models import Concept
from coding_systems.conftest import mock_migrate_coding_system
from coding_systems.versioning.models import CodingSystemRelease, ReleaseState


@pytest.fixture
def bnf_csr():
    def _csr(valid_from=datetime(2022, 11, 1)):
        return CodingSystemRelease.objects.create(
            coding_system="bnf",
            release_name="import-data",
            valid_from=valid_from,
            state=ReleaseState.READY,
        )

    return _csr


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
    csr = bnf_csr()
    setup_db(csr)
    yield csr
    cleanup_db(csr)


@pytest.fixture
def bnf_release_excl_last_concept(bnf_csr):
    # setup the database as a duplicate of the fixture one, omitting the last concept
    csr = bnf_csr(datetime(2022, 10, 1))
    setup_db(csr, exclude_last_concept=True)
    yield csr
    cleanup_db(csr)


@pytest.fixture
def bnf_releases(bnf_csr):
    # setup multiple databases as duplicates of the fixture one, with different dates

    # earlier than the release the codelist versions are created with
    csr_20190101 = bnf_csr(datetime(2019, 1, 1))
    setup_db(csr_20190101)
    # earlier than bnf_release_excl_last_concept
    csr_20220901 = bnf_csr(datetime(2022, 9, 1))
    setup_db(csr_20220901)
    # later than bnf_release_excl_last_concept
    csr_20221201 = bnf_csr(datetime(2022, 12, 1))
    setup_db(csr_20221201)

    yield

    for csr in [csr_20190101, csr_20220901, csr_20221201]:
        cleanup_db(csr)


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


def test_save_codelist_draft_updates_compatibility(
    bnf_version_with_search, coding_systems_tmp_path, bnf_release
):
    assert bnf_version_with_search.status == Status.DRAFT
    assert not bnf_version_with_search.compatible_releases.exists()
    save_draft_for_review(draft=bnf_version_with_search)

    assert bnf_version_with_search.compatible_releases.exists()


def test_save_codelist_draft_updates_compatibility_multiple_releases(
    bnf_version_with_search,
    coding_systems_tmp_path,
    bnf_releases,
    bnf_release_excl_last_concept,
):
    # In this test, we have a draft created with release `bnf_test_20200101`
    # The `bnf_releases` fixture gives us 3 other releases, which are duplicates
    # of the data in `bnf_test_20200101`, so would all be compatible
    # These have dates 20190901, 20221001, 20221201
    # bnf_release_excl_last_concept is not compatible, and has date 20221101

    # When the draft version is saved for review, releases with more recent valid_from
    # dates are checked for compatibility in order from oldest to newest. If a release
    # is found to be incompatible, no later releases are checked.
    #
    # i.e. for this draft, releases are checked in this order:
    # (bnf_import-data_20190901 is skipped because it's earlier than the draft's cs release)
    # 1) bnf_import-data_20220901: compatible
    # 2) bnf_import-data_20221101: incompatible
    # 3) bnf_import-data_20221201: compatible (but later than an incompatible release, so not checked)

    assert bnf_version_with_search.status == Status.DRAFT
    assert not bnf_version_with_search.compatible_releases.exists()
    save_draft_for_review(draft=bnf_version_with_search)

    assert bnf_version_with_search.compatible_releases.count() == 1
    assert (
        bnf_version_with_search.compatible_releases.first().database_alias
        == "bnf_import-data_20220901"
    )
