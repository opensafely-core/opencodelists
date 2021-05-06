import pytest

# This register_assert_rewrite must appear before the module is imported.
pytest.register_assert_rewrite("opencodelists.tests.fixtures")
from opencodelists.tests.fixtures import *  # noqa

pytest.register_assert_rewrite("codelists.tests.views.assertions")
pytest.register_assert_rewrite("opencodelists.tests.assertions")


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass
