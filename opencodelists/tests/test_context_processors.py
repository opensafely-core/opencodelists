from opencodelists.context_processors import (
    in_production,
    take_screenshots,
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


class TestTakeScreenshots:
    """Tests of the take_screenshots context processor."""

    def test_not_taking_screenshots(self, rf, settings):
        """Test when the site is not being used to take screenshots (TAKE_SCREENSHOTS=False)."""
        settings.TAKE_SCREENSHOTS = False
        request = rf.get("/")
        assert take_screenshots(request)["take_screenshots"] is False

    def test_taking_screenshots(self, rf, settings):
        """Test when the site is being used to take screenshots (TAKE_SCREENSHOTS=True)."""
        settings.TAKE_SCREENSHOTS = True
        request = rf.get("/")
        assert take_screenshots(request)["take_screenshots"] is True
