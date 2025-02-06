import pytest
from django.test import TestCase

from codelists.coding_systems import CODING_SYSTEMS


class DynamicDatabaseTestCase(TestCase):
    """A `django.test.TestCase` subclass to facilitate use of a dynamically
    created database.

    This class is necessary because some coding system tests currently use
    dynamically created databases at test time. Django 5.1 changed its behaviour
    such that the databases to be used must be specified when defining the test,
    and raises a `DatabaseOperationForbidden` error when accessing non-specified
    database.

    This class therefore allows additional database aliases to be specified,
    and modifies the `databases` attribute accordingly.

    For a more in-depth discussion, refer to the relevant issue:
    https://github.com/opensafely-core/opencodelists/issues/2115

    Also see the Django pull request that changed the Django behaviour:
    https://github.com/django/django/pull/17639

    import_data_path: name of the path to import data used, str or None
    """

    @property
    def db_alias(self):
        """The database alias that needs to be accessed in this test class, str."""
        raise NotImplementedError(
            "This test class requires a database alias to be set."
        )

    import_data_path = None

    def add_to_testcase_allowed_db_aliases(self, *db_aliases):
        """Add database names to the test instance's allowed database aliases.

        This mutates the *class* state by changing the `databases` attribute.
        The `databases` attribute determines which databases
        the `SimpleTestCase.ensure_connection_patch_method` allow connections to.

        This is used to allow access to dynamically generated databases that
        are creating during, and accessed in, tests.

        Note that we cannot patch this directly in a test case:
        pytest constructs its own dynamic test class based on the test case
        class defined in the test module, rather than instantiating an instance
        of that class directly.

        On first run, the originally allowed databases are recorded,
        for later restoration with `restore_original_testcase_db_aliases`.

        See https://docs.djangoproject.com/en/5.1/topics/testing/tools/#multi-database-support
        for details of the `databases` attribute being modified."""
        try:
            getattr(self, "original_databases")
        except AttributeError:
            # Record the original state, so we can later restore it.
            self.original_databases = type(self).databases

        type(self).databases |= frozenset({*db_aliases})

    def restore_original_testcase_db_aliases(self):
        """Restore the original `databases` attribute on the test case.

        `add_to_testcase_allowed_db_aliases` must have been run at least once.

        This removes any dynamic database that we have added to the test class.
        Django doesn't know how to roll back when the transaction wrapping the
        test case ends.

        It is not necessary to remove the database as the temp dir is scoped
        by test case."""
        type(self).databases = self.original_databases

    def setUp(self):
        super().setUp()

        self.add_to_testcase_allowed_db_aliases(self, self.db_alias)

    def tearDown(self):
        self.restore_original_testcase_db_aliases()

        super().tearDown()


class DynamicDatabaseTestCaseWithTmpPath(DynamicDatabaseTestCase):
    """A DynamicDatabaseTestCase subclass to facilitate use of a dynamically created database,
    for a subset of the coding systems tests that use the
    `coding_systems_tmp_path fixture` in `conftest.py`.

    That fixture creates temporary directories for *all* coding systems.

    coding_system_subpath_name: name of the coding system, that should be the same
    as the temporary database subpath in use for the test, str or None
    """

    @property
    def coding_system_subpath_name(self):
        # The db_alias that will be added temporarily to the DB.
        raise NotImplementedError(
            "This test class requires a coding system subpath name to be set."
        )

    @pytest.fixture(autouse=True)
    def _get_tmp_path(self, coding_systems_tmp_path):
        """Runs the fixture that creates a temporary path."""

        # The `coding_systems_tmp_path_fixture` creates directories
        # based on CODING_SYSTEMS.keys().
        # We can catch if a test has which paths are not allowed.
        allowed_coding_systems = CODING_SYSTEMS.keys()
        if self.coding_system_subpath_name not in allowed_coding_systems:
            raise ValueError(
                "The specified coding_system_subpath is not found in codelists.coding_systems.CODING_SYSTEMS."
            )

        self.coding_systems_tmp_path = coding_systems_tmp_path
        self.expected_db_path = (
            self.coding_systems_tmp_path
            / f"{self.coding_system_subpath_name}"
            / f"{self.db_alias}.sqlite3"
        )
