import pytest
from django.db import connections
from django.test import TestCase
from opentelemetry import trace
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from services.tracing import response_hook


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


@pytest.fixture(scope="session", autouse=True)
def testing_db_setup(django_db_modify_db_settings, django_db_blocker):
    """
    Set up the test databases for all configured databases aliases, including
    schema creation, before any test plan execution.

    For pytest to do this natively, we could alternatively mark up tests/modules with:
        pytest.mark.django_db(databases=['default', 'snomedct_test_20200101', 'dmd_test_20200101', 'bnf_test_20200101'])
    """
    for alias in connections.databases.keys():
        with django_db_blocker.unblock():
            # Does nothing if already exists -- as for 'default'.
            connections[alias].creation.create_test_db(verbosity=0, autoclobber=False)


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


@pytest.fixture(autouse=True)
def fast_password_hasher(settings):
    """Use a faster password hashing algorithm when running tests, as the test
    environment doesn't need to be as secure as production.
    """
    settings.PASSWORD_HASHERS = [
        "django.contrib.auth.hashers.MD5PasswordHasher",
    ]


################################################################################################################
# Setup global tracing infrastructure for testing purposes.

# The test setup is designed to be as close to the prod environment as possible,
# with only necessary modifications specific to testing.

# Create a resource for testing purposes with a unique 'service.name' value to
# minimise risk of mixing test and prod telemetry data.
# https://opentelemetry-python.readthedocs.io/en/latest/sdk/resources.html
resource = Resource.create(attributes={"service.name": "opencodelists-test"})

# Configure a global default OTel TracerProvider for our tests:
# The TracerProvider enables access to Tracers, Tracers create Spans.
# TracerProvider configuration is done once, globally, because the OTel Tracing API
# should be used to configure and set/register a global default TracerProvider once,
# at the start of a process (in this case, the pytest session; in prod, a gunicorn
# worker process)). This means that during the pytest test session any test
# that uses Django's test client will generate telemetry data (spans)
# that we can assert against.
# https://opentelemetry.io/docs/specs/otel/trace/api/#tracerprovider
provider = TracerProvider(resource=resource)
trace.set_tracer_provider(provider)

# In prod, we use the OTLPSpanExporter which exports our telemetry data to Honeycomb.
# In testing, we use InMemorySpanExporter() to collect spans locally, and assert
# against them during tests using the span_exporter fixture.
testing_span_exporter = InMemorySpanExporter()

# In prod, we use the BatchSpanProcessor as this is asynchronous, and queues
# and retries sending telemetry. In testing, we use SimpleSpanProcessor, which is
# synchronous and easy to inspect the output of within a test.
provider.add_span_processor(SimpleSpanProcessor(testing_span_exporter))

# Mirror production instrumentation:
# Use DjangoInstumentor() to instrument OpenCodelists test data, with prod response_hook().
DjangoInstrumentor().instrument(response_hook=response_hook)
################################################################################################################


@pytest.fixture(autouse=True)
def clear_testing_span_exporter():
    """Clear OTel spans from the test exporter after each test"""
    yield
    testing_span_exporter.clear()


@pytest.fixture
def span_exporter():
    """Provide access to the global span exporter for interrogation.
    Interrogate it with, for example, get_finished_spans()."""
    assert not testing_span_exporter.get_finished_spans()
    yield testing_span_exporter
