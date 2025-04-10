import pytest
from playwright.sync_api import expect

from coding_systems.base.tests.dynamic_db_classes import DynamicDatabaseTestCase
from opencodelists.models import User


pytestmark = pytest.mark.order("last")


class TestCodingSystem(DynamicDatabaseTestCase):
    db_alias = "bnf_test_20200101"

    @pytest.fixture(autouse=True)
    def get_client(self, client):
        self._client = client

    @pytest.fixture(autouse=True)
    def get_browser(self, browser):
        self._browser = browser

    @pytest.fixture(autouse=True)
    def get_live_server(self, live_server):
        self._live_server = live_server

    @pytest.mark.usefixtures("bnf_data_testing")
    def test_login_works(self):
        user = User.objects.create_user(
            username="functional",
            password="test_user",
            email="functional_test_user@example.com",
            name="Functional Test User",
        )
        user.save()
        self._client.force_login(user)
        user_cookies = {
            "name": "sessionid",
            "value": self._client.cookies["sessionid"].value,
            "url": self._live_server.url,
        }

        context = self._browser.new_context()
        context.add_cookies([user_cookies])
        page = context.new_page()
        page.goto(self._live_server.url)
        page.pause()
        expect(page.get_by_role("button", name="My account")).to_be_visible()
