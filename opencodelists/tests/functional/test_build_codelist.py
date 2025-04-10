import pytest
from playwright.sync_api import expect


pytestmark = pytest.mark.order("last")


@pytest.fixture
def _functional_test_user(functional_test_user):
    return functional_test_user


@pytest.fixture
def user_cookies(client, _functional_test_user, live_server):
    client.force_login(_functional_test_user)
    return {
        "name": "sessionid",
        "value": client.cookies["sessionid"].value,
        "url": live_server.url,
    }


@pytest.fixture
def login_context(browser, user_cookies):
    context = browser.new_context()
    context.add_cookies([user_cookies])
    return context


def test_login_works(login_context, user_without_organisation, live_server):
    page = login_context.new_page()
    page.goto(live_server.url)
    expect(page.get_by_role("button", name="My account")).to_be_visible()
