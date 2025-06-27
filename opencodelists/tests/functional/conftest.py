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
def login_context_for_user(browser, client, live_server):
    """A factory fixture that returns a function to create a login context
    for a given user, and optional organisation."""

    def _login_context_for_user(username, org=None):
        user = User.objects.create_user(
            username=username,
            password="test_user",
            email=f"{username}@example.com",
            name=f"{username} Test User",
        )
        if org:
            organisation = create_organisation(name=org, url="https://test.ac.uk")
            add_user_to_organisation(
                user=user, organisation=organisation, date_joined="2020-02-29"
            )
        client.force_login(user)
        cookies = {
            "name": "sessionid",
            "value": client.cookies["sessionid"].value,
            "url": live_server.url,
        }
        context = browser.new_context(locale="en-GB")
        context.add_cookies([cookies])
        return context

    return _login_context_for_user


@pytest.fixture
def non_organisation_login_context(login_context_for_user):
    return login_context_for_user("non_org_user")


@pytest.fixture
def organisation_login_context(login_context_for_user):
    return login_context_for_user("org_user", "Test University")
