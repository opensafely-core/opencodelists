import pytest
from playwright.sync_api import expect

from opencodelists.models import User


pytestmark = pytest.mark.functional


@pytest.fixture
def functional_test_user():
    return User.objects.create_user(
        username="functional",
        password="test_user",
        email="functional_test_user@example.com",
        name="Functional Test User",
    )


@pytest.fixture
def user_cookies(client, functional_test_user, live_server):
    client.force_login(functional_test_user)
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


def test_codelist_builder(login_context, user_without_organisation, live_server):
    page = login_context.new_page()
    page.goto(live_server.url)
    page.pause()
    expect(page.get_by_role("button", name="My account")).to_be_visible()


# Rudimentary codegen coding system builder form usage:
#    page.get_by_role("textbox", name="Codelist name*").fill("Test4")
#    page.get_by_label("Coding system*").select_option("snomedct")
#    page.get_by_role("button", name="Create").click()
#    page.get_by_role("searchbox", name="Term or code").click()
#    page.get_by_role("searchbox", name="Term or code").fill("arthritis")
#    page.get_by_role("searchbox", name="Term or code").press("Enter")
#    page.get_by_role("button", name="Search").click()
#    page.get_by_role("button", name="⊞").click()
#    page.get_by_role("button", name="+").first.click()
#    page.get_by_role("button", name="−").nth(1).click()
#    page.get_by_role("button", name="+").nth(2).click()
#    page.get_by_role("searchbox", name="Term or code").click()
#    page.get_by_role("searchbox", name="Term or code").fill("tennis")
#    page.get_by_role("searchbox", name="Term or code").press("Enter")
#    page.get_by_role("button", name="Search", exact=True).click()
#    page.get_by_role("button", name="−").nth(2).click()
#    page.get_by_role("button", name="Save draft").click()
