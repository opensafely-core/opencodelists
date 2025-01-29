import pytest
from django.test import TestCase


class DynamicDatabaseStateNotRecordedError(Exception):
    pass


class DynamicDatabaseTestCase(TestCase):
    @property
    def db_alias(self):
        # The db_alias that will be added temporarily to the DB.
        raise NotImplementedError(
            "This test class requires a database alias to be set."
        )

    # TODO:
    # coding_system is not used in every test.
    # We could consider making it optional.
    # It's currently required because we set the expected_db_path based on it,
    # even if that path is not used.
    @property
    def coding_system(self):
        raise NotImplementedError("This test class requires a coding system to be set.")

    # import_data_path is only used in some tests.
    import_data_path = None
    # needs_db_tmp_dir is only used for tests that write a database.
    needs_db_tmp_dir = False

    @pytest.fixture
    def _get_tmp_dir(self, coding_systems_database_tmp_dir):
        self.coding_systems_database_tmp_dir = coding_systems_database_tmp_dir
        self.expected_db_path = (
            self.coding_systems_database_tmp_dir
            / f"{self.coding_system}"
            / f"{self.db_alias}.sqlite3"
        )

    # This is a workaround to make using the _tmp_dir fixture configurable,
    # avoiding use of the coding_systems_database_tmp_dir fixture.
    # It may not be really necessary, nor may it be that useful.
    # (It's possible that the underlying fixture is run in conftest.py anyway.)
    # Only fixtures can access fixtures, and fixtures can't be called directly,
    # so we can't do this in setUp, I don't think.
    @pytest.fixture(autouse=True)
    def _configure_tmp_dir(self, request):
        if self.needs_db_tmp_dir:
            request.getfixturevalue("_get_tmp_dir")

    def add_to_databases(self, *args):
        try:
            getattr(self, "original_databases")
        except AttributeError:
            # Record the original state, so we can later restore it.
            self.original_databases = type(self).databases

        type(self).databases |= frozenset({*args})

    def restore_original_databases(self):
        try:
            getattr(self, "original_databases")
        except AttributeError:
            # The list of original databases was never set.
            # This should never happen for a test based on this class.
            # We record the state when first adding to the databases.
            raise DynamicDatabaseStateNotRecordedError
        else:
            # Remove the dynamic database from the test class, as Django doesn't
            # know how to roll back when the transaction wrapping the test case ends.
            type(self).databases = self.original_databases

    def setUp(self):
        super().setUp()

        # Mutate *class* state, this attribute determines to which databases
        # SimpleTestCase.ensure_connection_patch_method will allow connections.
        # We can't patch this directly in the test case as the class is
        # constructed dynamically. No need to reset as each test case execution
        # gets a new dynamic class.
        self.add_to_databases(self, self.db_alias)

        # Not necessary to remove the DB as the temp dir is scoped by test case.

    def tearDown(self):
        super().tearDown()
        self.restore_original_databases()
