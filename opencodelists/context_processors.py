from django.conf import settings


def in_production(request):
    """Is the site operating in production mode?

    As determined by settings.py / environment variables."""
    return {"in_production": settings.IN_PRODUCTION}


def take_screenshots(request):
    """Is the site being used to take screenshots?

    As determined by settings.py / environment variables."""
    return {"take_screenshots": settings.TAKE_SCREENSHOTS}
