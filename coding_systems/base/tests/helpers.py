import pytest
from django.test import TestCase


class DynamicDatabaseStateNotRecordedError(Exception):
    pass


class DynamicDatabaseTestCase(TestCase):
    """A special TestCase subclass to facilitate use of
    a dynamically created database.

    db_alias: name of the database that needs to be accessed, str (required)
    coding_system: name of the coding system, for generating a temporary
    database directory, str or None
    import_data_path: name of the path to import data used, str or None
    """

    @property
    def db_alias(self):
        # The db_alias that will be added temporarily to the DB.
        raise NotImplementedError(
            "This test class requires a database alias to be set."
        )

    coding_system = None
    import_data_path = None

    @pytest.fixture
    def _get_tmp_path(self, coding_systems_tmp_path):
        """Runs the fixture that creates a temporary path."""
        self.coding_systems_tmp_path = coding_systems_tmp_path
        self.expected_db_path = (
            self.coding_systems_tmp_path
            / f"{self.coding_system}"
            / f"{self.db_alias}.sqlite3"
        )

    @pytest.fixture(autouse=True)
    def _configure_tmp_path(self, request):
        if self.coding_system is not None:
            request.getfixturevalue("_get_tmp_path")

    def add_to_databases(self, *args):
        """Add database names to the test instance's allowed databases.

        On first run, the originally allowed databases are recorded,
        for later restoration with restore_original_databases."""
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
