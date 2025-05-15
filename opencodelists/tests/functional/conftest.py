import os
import subprocess
import sys

import pytest

from opencodelists.actions import (
    add_user_to_organisation,
    create_organisation,
)
from opencodelists.models import User


@pytest.fixture(scope="session", autouse=True)
def set_env():
    # This is required for playwright tests with Django
    # See https://github.com/microsoft/playwright-pytest/issues/29
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "1"


@pytest.fixture(scope="session", autouse=True)
def playwright_install(request):
    # As this can potentially take a long time when it's first run (and as it is
    # subsequently a silent no-op) we disable output capturing so that progress gets
    # displayed to the user
    capmanager = request.config.pluginmanager.getplugin("capturemanager")
    command = [sys.executable, "-m", "playwright", "install", "chromium"]
    # Install with dependencies in CI (but not in docker, as they've already
    # been installed in the image)
    if os.environ.get("CI") and not os.environ.get("DOCKER"):  # pragma: no cover
        command.extend(["--with-deps"])
    with capmanager.global_and_fixture_disabled():
        subprocess.run(command, check=True)


@pytest.fixture
def non_organisation_test_user():
    return User.objects.create_user(
        username="non_organisation",
        password="test_user",
        email="non_organisation_test_user@example.com",
        name="Non-Organisation Test User",
    )


@pytest.fixture
def non_organisation_user_cookies(client, non_organisation_test_user, live_server):
    client.force_login(non_organisation_test_user)
    return {
        "name": "sessionid",
        "value": client.cookies["sessionid"].value,
        "url": live_server.url,
    }


@pytest.fixture
def non_organisation_login_context(browser, non_organisation_user_cookies):
    context = browser.new_context()
    context.add_cookies([non_organisation_user_cookies])
    return context


@pytest.fixture
def organisation_test_user():
    organisation = create_organisation(name="Test University", url="https://test.ac.uk")
    user = User.objects.create_user(
        username="organisation",
        password="test_user",
        email="organisation_test_user@example.com",
        name="Organisation Test User",
    )
    add_user_to_organisation(
        user=user, organisation=organisation, date_joined="2020-02-29"
    )
    return user


@pytest.fixture
def organisation_user_cookies(client, organisation_test_user, live_server):
    client.force_login(organisation_test_user)
    return {
        "name": "sessionid",
        "value": client.cookies["sessionid"].value,
        "url": live_server.url,
    }


@pytest.fixture
def organisation_login_context(browser, organisation_user_cookies):
    context = browser.new_context()
    context.add_cookies([organisation_user_cookies])
    return context
