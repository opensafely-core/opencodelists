import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def set_env():
    # This is required for playwright tests with Django
    # See https://github.com/microsoft/playwright-pytest/issues/29
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "1"
