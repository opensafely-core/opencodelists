"""
Django settings for opencodelists project.

Generated by 'django-admin startproject' using Django 3.0.4.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""
import os
import sys
from pathlib import Path

import sentry_sdk
from django.contrib.messages import constants as messages
from environs import Env
from furl import furl
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import ignore_logger

from services.logging import logging_config_dict

# Patch sqlite3 to ensure recent version
__import__("pysqlite3")
sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")


# Read env file/vars
env = Env()
env.read_env()


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", False)

BASE_URLS = env.list("BASE_URLS", [])
# note localhost is required on production for dokku checks
BASE_URLS += ["http://localhost:8000"]

ALLOWED_HOSTS = [furl(base_url).host for base_url in BASE_URLS]

IN_PRODUCTION = env.bool("IN_PRODUCTION", False)

if IN_PRODUCTION:
    # This setting causes infinite redirects
    # SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# https://docs.djangoproject.com/en/4.0/ref/settings/#std:setting-CSRF_TRUSTED_ORIGINS
CSRF_TRUSTED_ORIGINS = BASE_URLS


# Application definition

INSTALLED_APPS = [
    "opencodelists",
    "builder",
    "codelists",
    "superusers",
    "coding_systems.versioning",
    "coding_systems.bnf",
    "coding_systems.ctv3",
    "coding_systems.dmd",
    "coding_systems.icd10",
    "coding_systems.readv2",
    "coding_systems.snomedct",
    "mappings.bnfdmd",
    "mappings.ctv3sctmap2",
    "mappings.rctctv3map",
    "corsheaders",
    "crispy_forms",
    "django_extensions",
    "debug_toolbar",
    "rest_framework",
    "rest_framework.authtoken",
    "taggit",
    "anymail",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django_structlog.middlewares.RequestMiddleware",
]

if not env.bool("DDT_ENABLED", False):
    # Django Debug Toolbar adds 77s to the load time of a large codelist!
    INSTALLED_APPS.remove("debug_toolbar")
    MIDDLEWARE.remove("debug_toolbar.middleware.DebugToolbarMiddleware")

ROOT_URLCONF = "opencodelists.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "opencodelists.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases
# Increase timeout from the default 15s to minimise "database is locked" errors
# see https://docs.djangoproject.com/en/4.0/ref/databases/#database-is-locked-errors

# The default database holds data for all apps/models (including CodingSystemVersion)
# EXCEPT the coding systems themselves.
# Coding systems are in separate databases, one db per coding system and version
# Coding system version db connections are added after the apps have loaded, using
# the data in the CodingSystemVersion table
# see coding_systems.versioning.models.update_coding_system_database_connections (called
# from coding_systems.versioning.apps)
DATABASES = {
    "default": env.dj_db_url("DATABASE_URL", "sqlite:///db.sqlite3"),
    "OPTIONS": {"timeout": 30},
}

DATABASE_DIR = env("DATABASE_DIR", BASE_DIR)  # location of sqlite files e.g. /storage/
DATABASE_DUMP_DIR = DATABASE_DIR / "sql_dump"

# Default type for auto-created primary keys
# https://docs.djangoproject.com/en/3.2/releases/3.2/#customizing-type-of-auto-created-primary-keys

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"


# Custom user model

AUTH_USER_MODEL = "opencodelists.User"

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

if IN_PRODUCTION:
    AUTH_PASSWORD_VALIDATORS = [
        {
            "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        },
        {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
        {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
        {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    ]

# Post-login
LOGIN_REDIRECT_URL = "codelists:index"


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/
STATICFILES_DIRS = [BASE_DIR / "static" / "dist"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = "/static/"

WHITENOISE_USE_FINDERS = True


# Logging
LOGGING = logging_config_dict


# Tests
TEST_RUNNER = "opencodelists.django_test_runner.PytestTestRunner"


# Crispy
CRISPY_TEMPLATE_PACK = "bootstrap4"


# Sentry
# ignore the request logging middleware, it creates ungrouped events by default
# https://docs.sentry.io/platforms/python/guides/logging/#ignoring-a-logger
ignore_logger("django_structlog.middlewares.request")

SENTRY_DSN = os.environ.get("SENTRY_DSN")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        send_default_pii=True,
    )

# CORS

CORS_ORIGIN_ALLOW_ALL = True


MARKDOWN_FILTER_WHITELIST_TAGS = [
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "a",
    "p",
    "ul",
    "li",
    "code",
    "em",
    "strong",
    "img",
    "hr",
]

MARKDOWN_FILTER_WHITELIST_ATTRIBUTES = [
    "class",
    "src",
    "href",
]

MARKDOWN_FILTER_WHITELIST_STYLES = []


# Login/logout config
LOGOUT_REDIRECT_URL = "/"


# Debug Toolbar
INTERNAL_IPS = [
    "127.0.0.1",
]

# Messages
# https://docs.djangoproject.com/en/3.0/ref/contrib/messages/
MESSAGE_TAGS = {
    messages.DEBUG: "alert-info",
    messages.INFO: "alert-info",
    messages.SUCCESS: "alert-success",
    messages.WARNING: "alert-warning",
    messages.ERROR: "alert-danger",
}

# EMAIL
# Anymail
ANYMAIL = {
    "MAILGUN_API_KEY": env.str("MAILGUN_API_KEY", default=None),
    "MAILGUN_API_URL": "https://api.eu.mailgun.net/v3",
    "MAILGUN_SENDER_DOMAIN": "mg.opencodelists.org",
}
EMAIL_BACKEND = env.str(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
DEFAULT_FROM_EMAIL = "no-reply@opencodelists.org"
SERVER_EMAIL = "tech@opensafely.org"
