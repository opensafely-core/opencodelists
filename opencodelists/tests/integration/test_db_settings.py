import pytest
from django.db.utils import ConnectionHandler


@pytest.mark.django_db
class TestDatabaseSettings:
    """Tests that our intended core DB settings will be correctly applied.

    I say 'will be' because tests can't actually access the prod core DB."""

    @pytest.fixture()
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
        cursor = connections["default"].cursor()
        yield cursor
        cursor.close()
        connections["default"].close()

    def test_database_pragma_busy_timeout(self, fresh_db_cursor):
        """Test that the `busy_timeout` parameter is set as we expect.

        We don't set this explicitly in settings, but Django defaults it to 5s."""
        assert fresh_db_cursor.execute("PRAGMA busy_timeout").fetchone()[0] == 5000
