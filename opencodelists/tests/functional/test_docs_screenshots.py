import pytest

from codelists import actions
from codelists.coding_systems import most_recent_database_alias
from codelists.models import Status

from .test_build_codelist import setup_playwright_page
from .utils import screenshot_element_with_padding


pytestmark = pytest.mark.functional


@pytest.mark.django_db(
    databases=[
        "default",
        "bnf_test_20200101",
        "dmd_test_20200101",
        "snomedct_test_20200101",
    ],
    transaction=True,
)
def test_generate_unauthenticated_screen_shots(
    page,
    live_server,
    collaborator,
    user_without_organisation,
    disorder_of_elbow_codes,
    user,
):
    """
    Any screenshots that require that a user is not logged in
    """
    page.goto(live_server.url)
    # The sign up/sign in buttons
    screenshot_element_with_padding(
        page,
        page.locator("#navbarSupportedContent ul"),
        "sign-up.png",
        extra={"height": -2},
    )

    # Create and publish an example codelist with good metadata
    cl = actions.create_codelist_with_codes(
        owner=user,
        name="Asplenia",
        coding_system_id="snomedct",
        coding_system_database_alias=most_recent_database_alias("snomedct"),
        codes=disorder_of_elbow_codes,
        description="Codes indicating diagnosis of asplenia or dysplenia (acquired or congenital)",
        methodology="""
This codelist was derived by the following method:

  - [Read 2 Codelist](http://localhost/) provided by LSHTM. See references for paper.
  - Codes from Quality Outcome Framework (QOF) were examined and relevant spleen codes taken
  - Codes from SNOMED were taken by searching for relevant spleen terms

These 3 lists were mapped into CTV3 by TPP to create one list. This list was examined by 2 people and the following logic applied (see github issue for more detail):

  - Splenomegaly or splenic cysts excluded as no evidence of reduced function
  - Congenital syphilis which appears in the list due to one code with congenital syphilitic splenomegaly was excluded. Congenital syphilitic splenomegaly was included however.
  - All unspecified injuries to spleen for example trauma were excluded except where removal of spleen was specified.
  - Removal of accessory spleen was excluded
""",
        references=[
            {"text": "Discussion on GitHub issue", "url": "http://example1.com"},
            {
                "text": "Grint DJ, McDonald HI, Walker JL, Amirthalingam G, Andrews N, Thomas S. Safety of inadvertent administration of live zoster vaccine to immunosuppressed individuals in a UK-based observational cohort analysis. BMJ Open. 2020;10(1):e034886.",
                "url": "http://example2.com",
            },
        ],
        signoffs=[
            {"user": collaborator.username, "date": "2020-04-14"},
            {"user": user_without_organisation.username, "date": "2020-06-02"},
        ],
        status=Status.UNDER_REVIEW,
    )
    actions.publish_version(version=cl.versions.get())

    page.goto(live_server.url + cl.get_absolute_url())
    # A codelist example
    screenshot_element_with_padding(
        page,
        page.locator("[role='main']"),
        "codelist-homepage.png",
        full_page=True,
        extra={"height": -200},
    )

    page.get_by_role("tab", name="Full list").click()
    page.get_by_role("searchbox", name="Search:").type("elbow")
    # The tab with the full list of codes in the codelist
    screenshot_element_with_padding(
        page,
        page.locator("div.col-md-9").filter(
            has=page.get_by_role("tabpanel", name="Full list")
        ),
        "full-list.png",
        full_page=True,
    )


def test_generate_non_org_user_screen_shots(
    live_server,
    non_organisation_login_context,
):
    """
    Any screenshots that require a logged in user who is not part of an organisation
    """
    page = setup_playwright_page(
        login_context=non_organisation_login_context,
        url=live_server.url,
    )
    page.goto(live_server.url)
    # The top menu after login
    screenshot_element_with_padding(
        page,
        page.locator("#navbarSupportedContent ul"),
        "my-codelists.png",
        extra={"height": -2},
    )


def test_generate_org_user_screen_shots(
    live_server,
    organisation_login_context,
):
    """
    Any screenshots that require a logged in user who is part of an organisation
    """
    page = setup_playwright_page(
        login_context=organisation_login_context,
        url=live_server.url,
    )
    page.goto(live_server.url)
    # The top menu after login
    screenshot_element_with_padding(
        page,
        page.locator("#navbarSupportedContent ul"),
        "my-organisations.png",
        extra={"height": -2},
    )
