from datetime import datetime

import pytest
from django.db import DEFAULT_DB_ALIAS, connections

from builder.actions import create_search
from builder.actions import save as save_draft_for_review
from codelists.coding_systems import CODING_SYSTEMS
from codelists.hierarchy import Hierarchy
from codelists.models import Status
from coding_systems.base.import_data_utils import update_codelist_version_compatibility
from coding_systems.base.tests.helpers import DynamicDatabaseTestCase
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


class BaseCodingSystemDynamicDatabaseTestCase(DynamicDatabaseTestCase):
    @pytest.fixture
    @pytest.mark.usefixtures("_bnf_release")
    def _get_bnf_release(self, _bnf_release):
        self.bnf_release = _bnf_release

    @pytest.fixture()
    def _bnf_release(self, bnf_csr):
        self.add_to_databases(self.db_alias)
        # setup the database as a duplicate of the fixture one
        csr = bnf_csr()
        setup_db(csr)
        yield csr
        cleanup_db(csr)

    @pytest.fixture
    @pytest.mark.usefixtures("_bnf_release_excl_last_concept")
    def _get_bnf_release_excl_last_concept(self, _bnf_release_excl_last_concept):
        self.bnf_release = _bnf_release_excl_last_concept

    @pytest.fixture
    def _bnf_release_excl_last_concept(self, bnf_csr):
        self.add_to_databases(self.db_alias)
        # setup the database as a duplicate of the fixture one, omitting the last concept
        csr = bnf_csr(datetime(2022, 10, 1))
        setup_db(csr, exclude_last_concept=True)
        yield csr
        cleanup_db(csr)

    @pytest.fixture
    @pytest.mark.usefixtures("_bnf_releases")
    def _get_bnf_releases(self, _bnf_releases):
        pass

    @pytest.fixture
    def _bnf_releases(self, bnf_csr):
        # TODO: remove horrible hack for testing.
        db_alias_additions = [
            "bnf_import-data_20190101",
            "bnf_import-data_20220901",
            "bnf_import-data_20221201",
        ]
        self.add_to_databases(*db_alias_additions)
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


class TestUpdateCodelistVersionCompatibilityNoSearches(
    BaseCodingSystemDynamicDatabaseTestCase
):
    db_alias = "bnf_import-data_20221101"
    coding_system = "bnf"

    @pytest.fixture(autouse=True)
    def _get_bnf_version_asthma(self, bnf_version_asthma):
        self.bnf_version_asthma = bnf_version_asthma

    #    @pytest.fixture(autouse=True)
    #    def _get_bnf_release(self, bnf_release):
    #        self.bnf_release = bnf_release

    @pytest.mark.usefixtures("_get_bnf_release")
    def test_update_codelist_version_compatibility_no_searches(self):
        # Draft versions are not checked for compatibility; this version is under review
        assert self.bnf_version_asthma.status == Status.PUBLISHED
        update_codelist_version_compatibility("bnf", self.bnf_release.database_alias)
        # this version has no searches, but its hierarchy is identical
        assert self.bnf_version_asthma.compatible_releases.exists()


class TestUpdateCodelistVersionDraftVersionExcluded(
    BaseCodingSystemDynamicDatabaseTestCase
):
    db_alias = "bnf_import-data_20221101"
    coding_system = "bnf"

    @pytest.fixture(autouse=True)
    def _get_bnf_version_with_search(self, bnf_version_with_search):
        self.bnf_version_with_search = bnf_version_with_search

    @pytest.mark.usefixtures("_get_bnf_release")
    def test_update_codelist_draft_version_excluded(self):
        assert self.bnf_version_with_search.status == Status.DRAFT
        update_codelist_version_compatibility("bnf", self.bnf_release.database_alias)
        # this version has an identical hierarchy, and its search will return the same
        # results with the new release, so it is compatible
        assert not self.bnf_version_with_search.compatible_releases.exists()


class TestUpdateCodelistVersionWithSearch(BaseCodingSystemDynamicDatabaseTestCase):
    db_alias = "bnf_import-data_20221101"
    coding_system = "bnf"

    @pytest.fixture(autouse=True)
    def _get_bnf_version_with_search(self, bnf_review_version_with_search):
        self.bnf_review_version_with_search = bnf_review_version_with_search

    @pytest.mark.usefixtures("_get_bnf_release")
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
    db_alias = "bnf_import-data_20221001"
    coding_system = "bnf"

    @pytest.fixture(autouse=True)
    def _get_bnf_version_with_search(self, bnf_review_version_with_search):
        self.bnf_review_version_with_search = bnf_review_version_with_search

    @pytest.mark.usefixtures("_get_bnf_release_excl_last_concept")
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
    db_alias = "bnf_import-data_20221001"
    coding_system = "bnf"

    @pytest.fixture(autouse=True)
    def _get_bnf_review_version_with_search(self, bnf_review_version_with_search):
        self.bnf_review_version_with_search = bnf_review_version_with_search

    @pytest.mark.usefixtures("_get_bnf_release_excl_last_concept")
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
    db_alias = "bnf_import-data_20221001"
    coding_system = "bnf"

    @pytest.fixture(autouse=True)
    def _get_bnf_version_with_search(self, bnf_version_with_search):
        self.bnf_version_with_search = bnf_version_with_search

    @pytest.mark.usefixtures("_get_bnf_release")
    def test_save_codelist_draft_updates_compatibility(self):
        assert self.bnf_version_with_search.status == Status.DRAFT
        assert not self.bnf_version_with_search.compatible_releases.exists()
        save_draft_for_review(draft=self.bnf_version_with_search)

        assert self.bnf_version_with_search.compatible_releases.exists()


class TestSaveCodelistDraftUpdatesCompatibilityMultipleReleases(
    BaseCodingSystemDynamicDatabaseTestCase
):
    # TODO: we need to specify multiple aliases.
    db_alias = "bnf_import-data_20190101"
    coding_system = "bnf"

    @pytest.fixture(autouse=True)
    def _get_bnf_version_with_search(self, bnf_version_with_search):
        self.bnf_version_with_search = bnf_version_with_search

    # TODO: not sure about this because of the use of multiple bnf_release/bnf_releases
    @pytest.mark.usefixtures("_get_bnf_releases", "_get_bnf_release_excl_last_concept")
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
