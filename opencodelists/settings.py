"""
Django settings for opencodelists project.

Generated by 'django-admin startproject' using Django 3.0.4.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
import re
import sys
from pathlib import Path

import dj_database_url
import sentry_sdk
from django.contrib.messages import constants as messages
from furl import furl
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import ignore_logger

from services.logging import logging_config_dict


# Patch sqlite3 to ensure recent version
__import__("sqlean")
sys.modules["sqlite3"] = sys.modules.pop("sqlean")


_missing_env_var_hint = """\
If you are running commands locally outside of `just` then you should
make sure that your `.env` file is being loaded into the environment,
which you can do in Bash using:

    set -a; source .env; set +a

If you are seeing this error when running via `just` (which should
automatically load variables from `.env`) then you should check that
`.env` contains all the variables listed in `dotenv-sample` (which may
have been updated since `.env` was first created).

If you are seeing this error in production then you haven't configured
things properly.
"""


def get_env_var(name):
    try:
        return os.environ[name]
    except KeyError:
        raise RuntimeError(
            f"Missing environment variable: {name}\n\n{_missing_env_var_hint}"
        )


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_env_var("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", default=False) == "True"

DEBUG_TOOLBAR = os.environ.get("DJANGO_DEBUG_TOOLBAR", default=False) == "True"

BASE_URLS = os.environ.get("BASE_URLS", default="").split(",")
# note localhost is required on production for dokku checks
BASE_URLS += ["http://localhost:7000"]

ALLOWED_HOSTS = [furl(base_url).host for base_url in BASE_URLS if base_url]

IN_PRODUCTION = os.environ.get("IN_PRODUCTION", default=False) == "True"

if IN_PRODUCTION:
    # This setting causes infinite redirects
    # SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# https://docs.djangoproject.com/en/4.0/ref/settings/#std:setting-CSRF_TRUSTED_ORIGINS
CSRF_TRUSTED_ORIGINS = BASE_URLS

# CSRF error view
# https://docs.djangoproject.com/en/4.1/ref/settings/#csrf-failure-view
CSRF_FAILURE_VIEW = "opencodelists.views.errors.csrf_failure"

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
    "mappings.dmdvmpprevmap",
    "corsheaders",
    "crispy_forms",
    "crispy_bootstrap4",
    "django_extensions",
    "rest_framework",
    "rest_framework.authtoken",
    "taggit",
    "anymail",
    "django_structlog",
    "django_vite",
    "slippers",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.humanize",
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
    "django_structlog.middlewares.RequestMiddleware",
]

if DEBUG_TOOLBAR:
    INSTALLED_APPS.append("debug_toolbar")
    MIDDLEWARE.append("debug_toolbar.middleware.DebugToolbarMiddleware")

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
                "opencodelists.context_processors.in_production",
            ],
            "builtins": ["slippers.templatetags.slippers"],
        },
    },
]

WSGI_APPLICATION = "opencodelists.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases
# Increase timeout from the default 15s to minimise "database is locked" errors
# see https://docs.djangoproject.com/en/4.0/ref/databases/#database-is-locked-errors

# The default database holds data for all apps/models (including CodingSystemRelease)
# EXCEPT the coding systems themselves.
# Coding systems are in separate databases, one db per coding system and version
# Coding system version db connections are added after the apps have loaded, using
# the data in the CodingSystemRelease table
# see coding_systems.versioning.models.update_coding_system_database_connections (called
# from coding_systems.versioning.apps)
DATABASES = {
    "default": {
        **dj_database_url.parse(
            os.environ.get("DATABASE_URL", default="sqlite:///db.sqlite3")
        ),
        "OPTIONS": {
            # Options used here are largely inspired by the article
            # https://kerkour.com/sqlite-for-servers
            # Note that Django actually sets the busy_timeout, synchronous, and
            # foreign_keys pragmas as we would like by default.
            # Tests of this behaviour in tests/integration/test_db_settings.py.
            "init_command": (
                # For documentation of these pragmas, see: https://www.sqlite.org/pragma.html.
                # Write-ahead logging journal mode writes transaction to a file
                # and then syncs them to the DB periodically. This stops writes
                # blocking reads and vice versa, without sacrificing
                # consistency guarantees.
                "PRAGMA journal_mode = WAL;"
                # The default cache size is 2MB but we can afford 125 times more!
                # Note negative values set cache size in KB, positive numbers
                # would set it by number of database pages.
                f"PRAGMA cache_size = -{250 * 1024};"
            ),
            # Transaction timeout in seconds. Increased from the default 5s as
            # it may help with the remaining "Database is locked" errors. See
            # https://github.com/opensafely-core/opencodelists/issues/2251 for
            # discussion. This affects PRAGMA busy_timeout. Increasing it
            # excessively may lead to worse UX for users that time out.
            "timeout": 15,
            #
            # Switch from SQLite's default DEFERRED transaction mode to IMMEDIATE. This
            # has the effect that write transactions will respect the busy timeout,
            # rather than failing immediately with "Database locked" if another write
            # transaction is in progress.
            # https://www.sqlite.org/lang_transaction.html#deferred_immediate_and_exclusive_transactions
            "transaction_mode": "IMMEDIATE",
        },
    }
}

DATABASE_DIR = Path(os.environ.get("DATABASE_DIR", default=BASE_DIR))
# location of sqlite files e.g. /storage/
CODING_SYSTEMS_DATABASE_DIR = DATABASE_DIR / "coding_systems"
DATABASE_ROUTERS = ["opencodelists.db_utils.CodingSystemReleaseRouter"]

# Default type for auto-created primary keys
# https://docs.djangoproject.com/en/3.2/releases/3.2/#customizing-type-of-auto-created-primary-keys

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"


# Custom user model

AUTH_USER_MODEL = "opencodelists.User"

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators


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


# https://docs.djangoproject.com/en/4.2/ref/contrib/staticfiles/#module-django.contrib.staticfiles
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# https://docs.djangoproject.com/en/5.0/howto/static-files/
# Note: these *must* be strings. If they are paths, we cannot cleanly extract them in ./scripts/collect-me-maybe.sh
BUILT_ASSETS = Path(
    os.environ.get("BUILT_ASSETS", default=BASE_DIR / "assets" / "dist")
)
STATICFILES_DIRS = [
    str(BASE_DIR / "static"),
    str(BUILT_ASSETS),
]
STATIC_ROOT = Path(os.environ.get("STATIC_ROOT", default=BASE_DIR / "staticfiles"))
STATIC_URL = "/static/"

ASSETS_DEV_MODE = os.environ.get("ASSETS_DEV_MODE", default=False) == "True"

DJANGO_VITE = {
    "default": {
        "dev_mode": ASSETS_DEV_MODE,
        "manifest_path": BUILT_ASSETS / ".vite" / "manifest.json",
    }
}

# Vite generates files with 8 hash digits
# http://whitenoise.evans.io/en/stable/django.html#WHITENOISE_IMMUTABLE_FILE_TEST


def immutable_file_test(path, url):
    # Match filename with 12 hex digits before the extension
    # e.g. app.db8f2edc0c8a.js
    return re.match(r"^.+[\.\-][0-9a-f]{8,12}\..+$", url)


WHITENOISE_IMMUTABLE_FILE_TEST = immutable_file_test


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

CORS_ALLOW_ALL_ORIGINS = True


MARKDOWN_FILTER_ALLOWLIST_TAGS = {
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "a",
    "p",
    "ol",
    "ul",
    "li",
    "code",
    "em",
    "strong",
    "img",
    "hr",
    "br",
}

MARKDOWN_FILTER_ALLOWLIST_ATTRIBUTES = {"*": {"class", "src", "href", "id"}}


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
    "MAILGUN_API_KEY": os.environ.get("MAILGUN_API_KEY", default=None),
    "MAILGUN_API_URL": "https://api.eu.mailgun.net/v3",
    "MAILGUN_SENDER_DOMAIN": "mg.opencodelists.org",
}
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
DEFAULT_FROM_EMAIL = "no-reply@opencodelists.org"
SERVER_EMAIL = "tech@opensafely.org"

# API key for dm+d imports
TRUD_API_KEY = get_env_var("TRUD_API_KEY")

# This setting will become the default in Django 6
# and can be removed when Opencodelists is upgraded to Django 6.
FORMS_URLFIELD_ASSUME_HTTPS = True

# Directory for image screenshots used in docs
SCREENSHOT_DIR = BASE_DIR / "static" / "img" / "docs"
