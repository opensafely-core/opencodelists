import pytest
from django.test import TestCase


# TODO: can we avoid using this fixture when not needed?
class DynamicDatabaseTestCase(TestCase):
    @property
    def db_alias(self):
        # The db_alias that will be added temporarily to the DB.
        raise NotImplementedError(
            "This test class requires a database alias to be set."
        )

    @property
    def coding_system(self):
        raise NotImplementedError("This test class requires a coding system to be set.")

    # TODO:
    # Remove autouse?
    # Find out if every coding system test really needs this.
    # Find out if we even need to have this setup in the class,
    # or can we just use the module-level fixture?
    @pytest.fixture(autouse=True)
    @pytest.mark.usefixtures("coding_systems_database_tmp_dir")
    def _get_tmp_dir(self, coding_systems_database_tmp_dir):
        self.coding_systems_database_tmp_dir = coding_systems_database_tmp_dir

    import_data_path = None
    original_databases = None

    @staticmethod
    def import_data_fixture(_):
        # Set to an import data fixture if required.
        raise NotImplementedError("This fixture function is optional.")

    def add_to_databases(self, *args):
        if self.original_databases is None:
            self.original_databases = type(self).databases
        type(self).databases |= frozenset({*args})

    def setUp(self):
        super().setUp()

        # Mutate *class* state, this attribute determines to which databases
        # SimpleTestCase.ensure_connection_patch_method will allow connections.
        # We can't patch this directly in the test case as the class is
        # constructed dynamically. No need to reset as each test case execution
        # gets a new dynamic class.
        self.add_to_databases(self, self.db_alias)

        try:
            self.expected_db_path = (
                self.coding_systems_database_tmp_dir
                / f"{self.coding_system}"
                / f"{self.db_alias}.sqlite3"
            )
        except NotImplementedError:
            self.expected_db_path = None

        # Set up mock source data.
        if self.import_data_path is None:
            try:
                self.import_data_path = next(
                    self.import_data_fixture(self.coding_systems_database_tmp_dir)
                )
            except NotImplementedError:
                self.import_data_path = None

        # Not necessary to remove the DB as the temp dir is scoped by test case.

    def tearDown(self):
        super().tearDown()
        # Remove the dynamic database from the test class, as Django doesn't
        # know how to roll back when the transaction wrapping the test case ends.
        type(self).databases = self.original_databases
