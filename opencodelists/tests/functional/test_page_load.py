import pytest
from playwright.sync_api import expect


pytestmark = pytest.mark.functional


def test_homepage_can_load(page, live_server):
    page.goto(live_server.url)
    expect(page.get_by_role("heading", name="OpenCodelists")).to_be_visible()
