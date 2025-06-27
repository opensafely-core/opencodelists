from opencodelists.context_processors import (
    in_production,
)


class TestInProduction:
    """Tests of the in_production context processor."""

    def test_in_production_mode(self, rf, settings):
        """Test when the site is in production mode (IN_PRODUCTION=False)."""
        settings.IN_PRODUCTION = False
        request = rf.get("/")
        assert in_production(request)["in_production"] is False

    def test_in_debug_mode(self, rf, settings):
        """Test when the site is in debug mode (IN_PRODUCTION=True)."""
        settings.IN_PRODUCTION = True
        request = rf.get("/")
        assert in_production(request)["in_production"] is True
