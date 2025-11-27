import json
from datetime import datetime

import pytest
from django.db import DEFAULT_DB_ALIAS, connections

from builder.actions import create_search
from builder.actions import save as save_draft_for_review
from codelists.coding_systems import CODING_SYSTEMS
from codelists.hierarchy import Hierarchy
from codelists.models import Status
from coding_systems.base.import_data_utils import update_codelist_version_compatibility
from coding_systems.base.tests.dynamic_db_classes import DynamicDatabaseTestCase
from coding_systems.bnf.models import Concept
from coding_systems.conftest import mock_migrate_coding_system
from coding_systems.versioning.models import CodingSystemRelease, ReleaseState


@pytest.fixture
def _bnf_csr():
    def _csr(valid_from=datetime(2022, 11, 1)):
        return CodingSystemRelease.objects.create(
            coding_system="bnf",
            release_name="import-data",
            valid_from=valid_from,
            state=ReleaseState.READY,
        )

    return _csr


@pytest.fixture
def _bnf_review_version_with_search(bnf_version_with_search):
    bnf_version_with_search.status = Status.UNDER_REVIEW
    bnf_version_with_search.save()
    yield bnf_version_with_search


class BaseCodingSystemDynamicDatabaseTestCase(DynamicDatabaseTestCase):
    @pytest.fixture
    def _bnf_release(self, _bnf_csr):
        # This addition of a allowed database alias needs to be done
        # *before* the class's setUp() runs.
        # This fixture is run before setUp() and
        # other fixtures required by this fixture access the database.
        self.add_to_testcase_allowed_db_aliases(self.db_aliases)

        # setup the database as a duplicate of the fixture one
        csr = _bnf_csr()
        _setup_db(csr)
        yield csr
        _cleanup_db(csr)

    @pytest.fixture
    def _get_bnf_release(self, _bnf_release):
        # This attribute is necessary for tests that need to access
        # the underlying CodingSystemRelease.
        # Currently, all tests only use one CodingSystemRelease.
        # It might be necessary to refactor how this attribute works
        # (maybe as a dictionary or similar) if any future tests require
        # accessing multiple CodingSystemReleases
        self.bnf_release = _bnf_release

    @pytest.fixture
    def _bnf_release_excl_last_concept(self, _bnf_csr):
        # This addition of a allowed database alias needs to be done
        # *before* the class's setUp() runs.
        # This fixture is run before setUp() and
        # other fixtures required by this fixture access the database.
        self.add_to_testcase_allowed_db_aliases(self.db_aliases)

        # setup the database as a duplicate of the fixture one, omitting the last concept
        csr = _bnf_csr(datetime(2022, 10, 1))
        _setup_db(csr, exclude_last_concept=True)
        yield csr
        _cleanup_db(csr)

    @pytest.fixture
    def _get_bnf_release_excl_last_concept(self, _bnf_release_excl_last_concept):
        self.bnf_release = _bnf_release_excl_last_concept

    @pytest.fixture
    def _bnf_releases(self, _bnf_csr):
        # This addition of a allowed database alias needs to be done
        # *before* the class's setUp() runs.
        # This fixture is run before setUp() and
        # other fixtures required by this fixture access the database.
        self.add_to_testcase_allowed_db_aliases(self.db_aliases)

        # setup multiple databases as duplicates of the fixture one, with different dates

        # earlier than the release the codelist versions are created with
        csr_20190101 = _bnf_csr(datetime(2019, 1, 1))
        _setup_db(csr_20190101)
        # earlier than bnf_release_excl_last_concept
        csr_20220901 = _bnf_csr(datetime(2022, 9, 1))
        _setup_db(csr_20220901)
        # later than bnf_release_excl_last_concept
        csr_20221201 = _bnf_csr(datetime(2022, 12, 1))
        _setup_db(csr_20221201)

        yield

        for csr in [csr_20190101, csr_20220901, csr_20221201]:
            _cleanup_db(csr)

    @pytest.fixture
    def _get_bnf_version_with_search(self, bnf_version_with_search):
        self.bnf_version_with_search = bnf_version_with_search

    @pytest.fixture
    def _get_bnf_review_version_with_search(self, _bnf_review_version_with_search):
        self.bnf_review_version_with_search = _bnf_review_version_with_search

    @pytest.fixture
    def _get_bnf_version_asthma(self, bnf_version_asthma):
        self.bnf_version_asthma = bnf_version_asthma


def _setup_db(csr, exclude_last_concept=False):
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


def _cleanup_db(csr):
    # The in-memory db doesn't get automatically removed, so manually drop the
    # tables for the next test
    with connections[csr.database_alias].cursor() as cursor:
        cursor.execute("DROP TABLE bnf_concept")


class TestUpdateCodelistVersionCompatibilityNoSearches(
    BaseCodingSystemDynamicDatabaseTestCase
):
    db_aliases = [
        "bnf_import-data_20221101",
    ]

    @pytest.mark.usefixtures("_get_bnf_release", "_get_bnf_version_asthma")
    def test_update_codelist_version_compatibility_no_searches(self):
        # Draft versions are not checked for compatibility; this version is under review
        assert self.bnf_version_asthma.status == Status.PUBLISHED
        update_codelist_version_compatibility("bnf", self.bnf_release.database_alias)
        # this version has no searches, but its hierarchy is identical
        assert self.bnf_version_asthma.compatible_releases.exists()


class TestUpdateCodelistVersionDraftVersionExcluded(
    BaseCodingSystemDynamicDatabaseTestCase
):
    db_aliases = [
        # _bnf_release
        "bnf_import-data_20221101",
    ]

    @pytest.mark.usefixtures("_get_bnf_release", "_get_bnf_version_with_search")
    def test_update_codelist_draft_version_excluded(self):
        assert self.bnf_version_with_search.status == Status.DRAFT
        update_codelist_version_compatibility("bnf", self.bnf_release.database_alias)
        # this version has an identical hierarchy, and its search will return the same
        # results with the new release, so it is compatible
        assert not self.bnf_version_with_search.compatible_releases.exists()


class TestUpdateCodelistVersionWithSearch(BaseCodingSystemDynamicDatabaseTestCase):
    db_aliases = [
        # _bnf_release
        "bnf_import-data_20221101",
    ]

    @pytest.mark.usefixtures("_get_bnf_release", "_get_bnf_review_version_with_search")
    def test_update_codelist_version_with_search(self):
        assert self.bnf_review_version_with_search.status == Status.UNDER_REVIEW
        update_codelist_version_compatibility("bnf", self.bnf_release.database_alias)
        # this version has an identical hierarchy, and its search will return the same
        # results with the new release, so it is compatible
        assert (
            self.bnf_review_version_with_search.compatible_releases.first()
            == self.bnf_release
        )


class TestUpdateCodelistVersionCompatibilityWithMismatchedSearch(
    BaseCodingSystemDynamicDatabaseTestCase
):
    db_aliases = [
        # _bnf_release_excl_last_concept
        "bnf_import-data_20221001",
    ]

    @pytest.mark.usefixtures(
        "_get_bnf_release_excl_last_concept", "_get_bnf_review_version_with_search"
    )
    def test_update_codelist_version_compatibility_with_mismatched_search(self):
        # setup the db, but omit the last Concept from the existing db, so the search
        # will return different results
        update_codelist_version_compatibility("bnf", self.bnf_release.database_alias)
        # this version has a search, but the new release returns different results,
        # so it is not compatible
        assert not self.bnf_review_version_with_search.compatible_releases.exists()


class TestUpdateCodelistVersionCompatibilityWithSearchButMismatchedHierarchy(
    BaseCodingSystemDynamicDatabaseTestCase
):
    db_aliases = [
        # _bnf_release_excl_last_concept
        "bnf_import-data_20221001",
    ]

    @pytest.mark.usefixtures(
        "_get_bnf_release_excl_last_concept", "_get_bnf_review_version_with_search"
    )
    def test_update_codelist_version_compatibility_with_search_but_mismatched_hierarchy(
        self,
    ):
        # setup the db, but omit the last Concept from the existing db
        # Modify the search so that it returns just one code; the hierarchy will differ but
        # search results will remain the same
        self.bnf_review_version_with_search.searches.all().delete()
        create_search(
            draft=self.bnf_review_version_with_search,
            code="0301012A0AAABAB",
            codes=["0301012A0AAABAB"],
        )

        existing_hierarchy = self.bnf_review_version_with_search.hierarchy
        hierarchy_with_new_release = Hierarchy.from_codes(
            coding_system=CODING_SYSTEMS["bnf"](
                database_alias=self.bnf_release.database_alias
            ),
            codes=["0301012A0AAABAB"],
        )
        assert existing_hierarchy.nodes != hierarchy_with_new_release.nodes

        update_codelist_version_compatibility("bnf", self.bnf_release.database_alias)
        # this version has a search that returns identical results in the new release
        # but the hierarchies differ, so it is not compatible
        assert not self.bnf_review_version_with_search.compatible_releases.exists()


class TestSaveCodelistDraftUpdatesCompatibility(
    BaseCodingSystemDynamicDatabaseTestCase
):
    db_aliases = [
        # _bnf_releases
        "bnf_import-data_20190101",
        "bnf_import-data_20220901",
        "bnf_import-data_20221201",
    ]

    @pytest.mark.usefixtures(
        "_bnf_releases",
        "_get_bnf_version_with_search",
    )
    def test_save_codelist_draft_updates_compatibility(self):
        assert self.bnf_version_with_search.status == Status.DRAFT
        assert not self.bnf_version_with_search.compatible_releases.exists()
        save_draft_for_review(draft=self.bnf_version_with_search)

        assert self.bnf_version_with_search.compatible_releases.exists()


class TestSaveCodelistDraftUpdatesCompatibilityMultipleReleases(
    BaseCodingSystemDynamicDatabaseTestCase
):
    db_aliases = [
        # _bnf_releases
        "bnf_import-data_20190101",
        "bnf_import-data_20220901",
        "bnf_import-data_20221201",
        # _bnf_release_excl_last_concept
        "bnf_import-data_20221001",
    ]

    @pytest.mark.usefixtures(
        "_bnf_releases",
        "_bnf_release_excl_last_concept",
        "_get_bnf_version_with_search",
    )
    def test_save_codelist_draft_updates_compatibility_multiple_releases(self):
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

        assert self.bnf_version_with_search.status == Status.DRAFT
        assert not self.bnf_version_with_search.compatible_releases.exists()
        save_draft_for_review(draft=self.bnf_version_with_search)

        assert self.bnf_version_with_search.compatible_releases.count() == 1
        assert (
            self.bnf_version_with_search.compatible_releases.first().database_alias
            == "bnf_import-data_20220901"
        )


class TestUpdateCodelistVersionCompatibilityIsOrderInsensitive(
    BaseCodingSystemDynamicDatabaseTestCase
):
    db_aliases = [
        "bnf_import-data_20221101",
    ]

    @pytest.mark.usefixtures("_get_bnf_release", "_get_bnf_review_version_with_search")
    def test_update_codelist_version_compatibility_is_order_insensitive(
        self,
    ):
        # modify the cached hierarchy data such that order of list elements is reversed
        modified_existing_cached_hierarchy = json.loads(
            self.bnf_review_version_with_search.cached_hierarchy.data
        )
        modified_existing_cached_hierarchy["nodes"] = list(
            reversed(modified_existing_cached_hierarchy["nodes"])
        )
        modified_existing_cached_hierarchy["child_map"] = {
            k: list(reversed(v))
            for k, v in modified_existing_cached_hierarchy["child_map"].items()
        }
        modified_existing_cached_hierarchy["parent_map"] = {
            k: list(reversed(v))
            for k, v in modified_existing_cached_hierarchy["parent_map"].items()
        }
        modified_existing_cached_hierarchy_data = json.dumps(
            modified_existing_cached_hierarchy
        )
        assert (
            modified_existing_cached_hierarchy_data
            != self.bnf_review_version_with_search.cached_hierarchy.data
        )

        self.bnf_review_version_with_search.cached_hierarchy.data = (
            modified_existing_cached_hierarchy_data
        )
        self.bnf_review_version_with_search.cached_hierarchy.save()

        update_codelist_version_compatibility("bnf", self.bnf_release.database_alias)
        assert self.bnf_review_version_with_search.compatible_releases.exists()
