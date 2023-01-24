import re
from pathlib import Path
from urllib.parse import urljoin

import pytest
from django.core.management import call_command
from playwright.sync_api import expect

from codelists.models import Codelist
from opencodelists.models import User

pytestmark = pytest.mark.e2e

SCREENSHOT_DOCS_DIR = Path(__file__).parent / "screenshots" / "docs"
FIXTURES_PATH = Path(__file__).parent / "fixtures"
TEST_NAME_REGEX = re.compile(r"test_(?P<screenshot_name>.+)\[.+\]")


@pytest.fixture(autouse=True)
def setup_e2e():
    call_command(
        "loaddata",
        FIXTURES_PATH / "default_db.json",
        database="default",
    )


@pytest.fixture()
def snomedct():
    call_command(
        "loaddata",
        FIXTURES_PATH / "snomedct_version-xx_20221101.json",
        database="snomedct_version-xx_20221101",
    )


@pytest.fixture
def e2e_version(snomedct):
    yield Codelist.objects.filter(
        coding_system_id="snomedct"
    ).last().latest_published_version()


@pytest.fixture
def e2e_under_review_version(snomedct, org_user):
    yield Codelist.objects.filter(
        coding_system_id="snomedct"
    ).last().latest_visible_version(user=org_user)


@pytest.fixture
def org_user():
    yield User.objects.get(username="jsmith")


@pytest.fixture
def name_of_test(request):
    yield request.node.name


@pytest.fixture
def logged_in_context(live_server, browser, context, org_user):
    state_path = Path(__file__).parent / "context_state.json"
    if not state_path.exists():
        context = browser.new_context(storage_state=state_path)
    else:
        page = context.new_page()
        page.goto(urljoin(live_server.url, "accounts/login/"))
        page.locator("#id_username").fill(org_user.username)
        page.locator("#id_password").fill("test")
        page.get_by_role("button", name="Sign in").click()
        context.storage_state(path=state_path)
    yield context


def take_screenshot_for_docs(page_or_element, name_of_test, name, full_page=False):
    name_match = TEST_NAME_REGEX.match(name_of_test)
    kwargs = {"full_page": full_page} if full_page else {}
    page_or_element.screenshot(
        path=SCREENSHOT_DOCS_DIR / f"{name_match['screenshot_name']}_{name}.png",
        **kwargs,
    )


@pytest.mark.django_db(databases=["default", "snomedct_version-xx_20221101"])
def test_viewing_a_codelist(
    name_of_test, logged_in_context, live_server, e2e_version, e2e_under_review_version
):
    page = logged_in_context.new_page()
    page.goto(urljoin(live_server.url, e2e_version.get_absolute_url()))

    # main page
    main_page = page.get_by_role("main")
    codelist_name = main_page.locator("h3")
    expect(codelist_name).to_contain_text("Disorder of elbow")
    take_screenshot_for_docs(main_page, name_of_test, "main_page")

    # tabs
    tabs = page.locator("#tab-list").first
    # get the parent of the tabs for the screenshots
    tab_parent = tabs.locator("xpath=..")

    # about tab is shown by default
    about_tab = page.locator("#about")
    expect(about_tab).to_have_class(re.compile(r"show"))

    # full list
    expect(tabs).to_contain_text("Full list")
    full_list_tab_link = page.locator("#full-list-tab")
    full_list_tab_link.click()
    full_list_tab = page.locator("#full-list")
    expect(full_list_tab).to_have_class(re.compile(r"show"))
    take_screenshot_for_docs(tab_parent, name_of_test, "full_list_tab")

    # tree tab
    expect(tabs).to_contain_text("Tree")
    tree_tab_link = page.locator("#tree-tab")
    tree_tab_link.click()
    tree_tab = page.locator("#tree")
    expect(tree_tab).to_have_class(re.compile(r"show"))
    take_screenshot_for_docs(tab_parent, name_of_test, "tree_tab")

    # search tab
    page.goto(urljoin(live_server.url, e2e_under_review_version.get_absolute_url()))
    tabs = page.locator("#tab-list").first
    tab_parent = tabs.locator("xpath=..")
    expect(tabs).to_contain_text("Searches")
    searches_tab_link = page.locator("#search-results-tab")
    searches_tab_link.click()
    searches_tab = page.locator("#search-results")
    expect(searches_tab).to_have_class(re.compile(r"show"))
    take_screenshot_for_docs(tab_parent, name_of_test, "searches_tab")

    # download csv
    download_button = page.get_by_role("button", name="Download CSV")
    download_container = download_button.locator("xpath=..")
    expect(download_container).to_contain_text("Download definition")
    take_screenshot_for_docs(download_container, name_of_test, "download_csv")

    # versions


# def test_creating_an_account_nav():
#     ...


# def test_organisation_nav():
#     ...

# def test_my_codelists_nav():
#     ...


# def test_create_a_codelist_button():
#     ...


# def test_create_codelist_form():
#     ...
