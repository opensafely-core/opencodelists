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


@pytest.mark.django_db(
    databases=[
        "default",
        "snomedct_test_20200101",
        "dmd_test_20200101",
        "bnf_test_20200101",
    ],
    transaction=True,
)
def test_codelist_builder(login_context, user_without_organisation, live_server):
    page = login_context.new_page()
    page.goto(live_server.url)
    expect(page.get_by_role("button", name="My account")).to_be_visible()

    # Navigate to codelists.
    page.get_by_role("link", name="My codelists").click()
    page.get_by_role("link", name="Create a codelist!").click()

    # Complete the form to create a codelist.
    page.get_by_role("textbox", name="Codelist name *").fill("Test")
    page.get_by_label("Coding system *").select_option("snomedct")
    page.get_by_role("button", name="Create").click()

    # Make a search.
    page.get_by_role("searchbox", name="Term or code").click()
    page.get_by_role("searchbox", name="Term or code").fill("arthritis")
    page.get_by_role("searchbox", name="Term or code").press("Enter")
    page.get_by_role("button", name="Search", exact=True).click()

    # Select some of the hierarchy.
    page.get_by_role("button", name="⊞").click()
    page.get_by_role("button", name="+").first.click()
    page.get_by_role("button", name="−").nth(1).click()
    page.get_by_role("button", name="+").nth(2).click()

    # Make another search.
    page.get_by_role("searchbox", name="Term or code").click()
    page.get_by_role("searchbox", name="Term or code").fill("tennis")
    page.get_by_role("searchbox", name="Term or code").press("Enter")
    page.get_by_role("button", name="Search", exact=True).click()

    # Select some of the hierarchy.
    page.get_by_role("button", name="−").nth(2).click()

    # Finish working on the codelist.
    page.get_by_role("button", name="Save draft").click()
