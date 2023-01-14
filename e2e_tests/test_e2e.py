import re
from pathlib import Path

import pytest
from playwright.sync_api import expect

SCREENSHOT_DIR = Path(__file__).parent / "screenshots"


@pytest.mark.e2e
def test_screenshots(
    context,
    live_server,
    minimal_draft,
    organisation_user,
):
    # Start tracing
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    page = context.new_page()

    # homepage
    page.goto(live_server.url)
    # Check we're on the homepage
    expect(page).to_have_title(re.compile("OpenCodelists"))
    expect(page.get_by_role("main")).to_contain_text("Welcome to OpenCodelists")
    # It has 2 buttons, for search and reset
    buttons = page.get_by_role("button")
    assert buttons.all_inner_texts() == ["Search", "Reset"]
    page.screenshot(full_page=True, path=SCREENSHOT_DIR / "homepage_not_logged_in.png")

    # Find the Sign in link
    sign_in = page.get_by_role("link", name="Sign in")
    expect(sign_in).to_have_attribute("href", "/accounts/login/")
    # Click the Sign in link.
    sign_in.click()

    # Expects the URL to contain the login.
    expect(page).to_have_url(re.compile(".accounts/login/"))
    page.screenshot(path=SCREENSHOT_DIR / "sign_in.png")

    # Sign in
    username = page.locator("#id_username")
    password = page.locator("#id_password")
    sign_in_button = page.get_by_role("button", name="Sign in")
    # organisation_user's username/password are "bob"/"test"
    username.fill(organisation_user.username)
    password.fill("test")
    # click to login
    sign_in_button.click()

    # Goes back to homepage again after logging in
    page.wait_for_load_state()
    expect(page.get_by_role("main")).to_contain_text("Welcome to OpenCodelists")
    # Find the My Codelists link
    my_codelists = page.get_by_role("link", name="My codelists")
    expect(my_codelists).to_have_attribute("href", "/users/bob/")
    page.screenshot(full_page=True, path=SCREENSHOT_DIR / "homepage_logged_in.png")

    # View a codelist
    codelist_link = page.get_by_role("link", name="Minimal Codelist")
    codelist_link.click()

    # The latest version that this user has access to is a draft, so the link opens the builder page
    expect(page).to_have_url(re.compile(f".*{minimal_draft.get_builder_draft_url()}"))
    page.screenshot(
        full_page=True, path=SCREENSHOT_DIR / "minimal_codelist_builder.png"
    )

    builder = page.locator("#codelist-builder-container")
    expect(builder).to_be_visible()
    # This codelist has 4 codes
    #   35185008   Enthesopathy of elbow region
    #   73583000   └ Epicondylitis
    #   202855006    └ Lateral epicondylitis
    #   238484001  Tennis toe
    # by default the builder only expands one level deep
    assert set(minimal_draft.codes) == {
        "35185008",
        "73583000",
        "202855006",
        "238484001",
    }
    for code in set(minimal_draft.codes) - {"202855006"}:
        tree_item = builder.locator(f'css=[data-code="{code}"]')
        expect(tree_item).to_be_visible()
    collapsed_item = builder.locator('css=[data-code="202855006"]')
    expect(collapsed_item).to_be_hidden()

    # find the parent of the collapsed code
    parent = builder.locator('css=[data-code="73583000"]')
    expand_button = parent.get_by_text("⊞")
    expand_button.click()

    # Now all included codes are visible
    for code in set(minimal_draft.codes):
        tree_item = builder.locator(f'css=[data-code="{code}"]')
        expect(tree_item).to_be_visible(timeout=10000)

    page.screenshot(
        full_page=True, path=SCREENSHOT_DIR / "minimal_codelist_expanded_tree.png"
    )

    # Stop tracing and export it into a zip archive.
    context.tracing.stop(path=SCREENSHOT_DIR / "trace.zip")
