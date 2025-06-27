from django.conf import settings


def in_production(request):
    """Is the site operating in production mode?

    As determined by settings.py / environment variables."""
    return {"in_production": settings.IN_PRODUCTION}
