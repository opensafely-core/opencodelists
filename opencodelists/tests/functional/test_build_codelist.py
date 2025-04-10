import pytest
from playwright.sync_api import expect

from opencodelists.models import User


pytestmark = pytest.mark.order("last")


@pytest.fixture
def login_context(client, live_server, browser):
    user = User.objects.create_user(
        username="functional",
        password="test_user",
        email="functional_test_user@example.com",
        name="Functional Test User",
    )
    user.save()
    client.force_login(user)
    user_cookies = {
        "name": "sessionid",
        "value": client.cookies["sessionid"].value,
        "url": live_server.url,
    }

    context = browser.new_context()
    context.add_cookies([user_cookies])
    return context


def test_login_works(login_context, live_server):
    page = login_context.new_page()
    page.goto(live_server.url)
    page.pause()
    expect(page.get_by_role("button", name="My account")).to_be_visible()
