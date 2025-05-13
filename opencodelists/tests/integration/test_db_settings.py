import pytest
from django.db import ConnectionHandler, connection, transaction
from django.db.backends.utils import CursorWrapper
from django.test.utils import CaptureQueriesContext


def _assert_pragma(cursor: CursorWrapper, name: str, value: str | int):
    assert cursor.execute(f"PRAGMA {name}").fetchone()[0] == value


@pytest.mark.django_db
class TestDatabaseSettings:
    """Tests that our intended core DB settings will be correctly applied.

    I say 'will be' because tests can't actually access the prod core DB. So
    the tests that rely on the database state can't test that directly."""

    @pytest.fixture
    def fresh_db_cursor(self, settings, tmp_path):
        """Provide a cursor for a connection to a freshly-created
        filesystem-based database based on the core default configuration.

        The standard test database is memory-based, and may be configured
        differently, so we don't just check against that. Scope is
        test-function to avoid any interaction between tests.
        """
        tmp_db_path = tmp_path / "test.db"
        connections = ConnectionHandler(
            {
                "default": {
                    **settings.DATABASES["default"],
                    "NAME": tmp_db_path,
                },
            }
        )
        self.connection = connections["default"]
        cursor = self.connection.cursor()
        yield cursor
        cursor.close()
        self.connection.close()

    def test_database_pragma_busy_timeout(self, fresh_db_cursor):
        """Test that the `busy_timeout` parameter is set as we expect.

        Django defaults it to 5s but we override in settings. Let's check."""
        # https://www.sqlite.org/pragma.html#pragma_busy_timeout
        # 15 seconds in milliseconds == 15000.
        _assert_pragma(fresh_db_cursor, "busy_timeout", 15000)

    def test_database_pragma_journal_mode(self, fresh_db_cursor):
        """Test that the `journal_mode` parameter is set as we expect."""
        # https://www.sqlite.org/pragma.html#pragma_journal_mode
        # 'wal' = write-ahead logging mode
        _assert_pragma(fresh_db_cursor, "journal_mode", "wal")

    def test_database_pragma_synchronous(self, fresh_db_cursor):
        """Test that the `synchronous` parameter is set as we expect."""
        # https://www.sqlite.org/pragma.html#pragma_synchronous
        # 2 == NORMAL
        _assert_pragma(fresh_db_cursor, "synchronous", 2)

    def test_database_pragma_cache_size(self, fresh_db_cursor):
        """Test that the `cache_size` parameter is set as we expect."""
        # https://www.sqlite.org/pragma.html#pragma_cache_size
        # -256000 = 200 * 1024Kb = 250MB. Negative indicates KB measurement.
        _assert_pragma(fresh_db_cursor, "cache_size", -256000)

    def test_database_pragma_foreign_keys(self, fresh_db_cursor):
        """Test that the `foreign_keys` parameter is set as we expect.

        We don't explicitly set this, Django does. Let's check."""
        # https://www.sqlite.org/pragma.html#pragma_foreign_keys
        # C boolean, 1 = True
        _assert_pragma(fresh_db_cursor, "foreign_keys", 1)

    @pytest.mark.django_db(transaction=True)
    def test_transaction_mode_immediate(self):
        """Test that Django opens connections in IMMEDIATE mode."""
        # Note that this test doesn't care about any property of the database
        # other than that it's a sqlite3 database, so there's no need to use
        # the fresh_db_cursor fixture, the normal in-memory test database works
        # fine.
        with CaptureQueriesContext(connection) as ctx:
            with transaction.atomic():
                pass
        assert ctx.captured_queries[0]["sql"] == "BEGIN IMMEDIATE"
