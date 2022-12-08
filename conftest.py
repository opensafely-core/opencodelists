import pytest
from django.db import connections
from django.test import TestCase

# TestCase.databases sets the databases that tests have access to; this allows all tests
# access to the test coding system databases in addition to the default db
database_aliases = {
    "default",
    "snomedct_test_20200101",
    "dmd_test_20200101",
    "icd10_test_20200101",
    "ctv3_test_20200101",
    "bnf_test_20200101",
}
TestCase.databases = database_aliases

# This register_assert_rewrite must appear before the module is imported.
pytest.register_assert_rewrite("opencodelists.tests.fixtures")
from opencodelists.tests.fixtures import *  # noqa

pytest.register_assert_rewrite("codelists.tests.views.assertions")
pytest.register_assert_rewrite("opencodelists.tests.assertions")


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass


@pytest.fixture(scope="session")
def django_db_modify_db_settings():
    """
    This is a pytest-django fixture called in the `django_db_setup` fixture, and
    provides a hook for modifying the DATABASES setting prior to test db configuration.
    It's used here to add in the test coding system dbs.  This needs to be done here,
    rather than calling  `versioning.models.update_coding_system_database_connections`
    so that the database connections are available at the point where the tests load the
    coding system fixtures, which is prior to db configuration.

    In addition, if the tests are running in a local environment with a database that contains
    CodingSystemReleases, the `update_coding_system_database_connections` command that
    runs on app startup will have populated the DATABASES setting with real release dbs
    so we also need to reset those before the tests start.
    """
    from django.conf import settings

    # Copy the default db configuration to each of the aliases; in the test setup the databases
    # are all in-memory sqlite databases, so although we're duplicating the configuration, the
    # databases in the tests will all be separate in-memory sqlite dbs
    coding_system_db_aliases = database_aliases - {"default"}

    # Reset the DATABASES settings so that it contains only the default db
    initial_database_aliases = settings.DATABASES.keys() - {"default", "OPTIONS"}
    for alias in initial_database_aliases:
        del settings.DATABASES[alias]

    for alias in coding_system_db_aliases:
        settings.DATABASES[alias] = dict(settings.DATABASES["default"])


@pytest.fixture(autouse=True)
def reset_connections():
    """
    Database connections are added based on the CodingSystemReleases that exist in the default
    database (see coding_systems.versioning.models.update_coding_system_database_connections).
    Ensure we remove these after tests.
    """
    initial_databases = set(connections.databases.keys())
    yield
    databases_added_during_tests = set(connections.databases.keys()) - initial_databases
    for db in databases_added_during_tests:
        del connections.databases[db]
