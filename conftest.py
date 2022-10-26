import pytest
from django.db import connections

# This register_assert_rewrite must appear before the module is imported.
pytest.register_assert_rewrite("opencodelists.tests.fixtures")
from opencodelists.tests.fixtures import *  # noqa

pytest.register_assert_rewrite("codelists.tests.views.assertions")
pytest.register_assert_rewrite("opencodelists.tests.assertions")


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass


@pytest.fixture(autouse=True)
def reset_connections():
    """
    Database connections are added based on the CodingSystemVersions that exist in the default
    database (see coding_systems.versioning.models.update_coding_system_database_connections).
    Ensure we remove these after tests.
    """
    initial_databases = set(connections.databases.keys())
    yield
    databases_added_during_tests = set(connections.databases.keys()) - initial_databases
    for db in databases_added_during_tests:
        del connections.databases[db]
