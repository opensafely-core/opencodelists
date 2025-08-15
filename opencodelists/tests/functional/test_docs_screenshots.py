import pytest

from codelists import actions
from codelists.coding_systems import most_recent_database_alias
from codelists.models import Status

from .test_build_codelist import (
    ConceptSelection,
    ConceptState,
    Navigator,
    Search,
    SearchAction,
    SearchActions,
    create_codelist,
    save_codelist_for_review,
    setup_playwright_page,
)
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

    # The download buttons
    screenshot_element_with_padding(
        page,
        page.locator("div.version__sidebar form"),
        "download-buttons.png",
        full_page=True,
    )


@pytest.mark.django_db(
    databases=[
        "default",
        "bnf_test_20200101",
    ],
    transaction=True,
)
def test_generate_non_org_user_screen_shots(
    live_server,
    non_organisation_login_context,
    bnf_data,
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

    # Creating a BNF codelist so we can show the "Convert to dm+d" button.
    coding_system = "bnf"
    codelist_name = "Asthma"

    navigator = Navigator(page, codelist_name)
    create_codelist(navigator, coding_system, initial_page_navigation=True)

    search_actions = SearchActions(
        items=[
            SearchAction(
                search=Search(query="asthma", is_code=False),
                concept_selections=[
                    ConceptSelection(
                        code="0301012A0AA",
                        term="Adrenaline (Asthma)",
                        to_expand=False,
                        state=ConceptState.INCLUDED,
                    ),
                ],
            ),
        ],
    )
    search_actions.apply_all(navigator)
    save_codelist_for_review(navigator)

    screenshot_element_with_padding(
        page,
        page.get_by_role("button", name="Convert to dm+d").locator(".."),
        "download-convert-buttons-bnf.png",
    )


@pytest.mark.django_db(
    databases=[
        "default",
        "snomedct_test_20200101",
    ],
    transaction=True,
)
def test_generate_org_user_screen_shots(
    live_server,
    organisation_login_context,
    snomedct_data,
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

    # Create a codelist button.
    page.get_by_role("link", name="My codelists").click()
    screenshot_element_with_padding(
        page,
        page.get_by_role("link", name="Create a codelist!"),
        "create-codelist-button.png",
    )

    page.get_by_role("link", name="Create a codelist!").click()

    page.get_by_role("textbox", name="Codelist name *").fill("Tennis elbow")
    page.get_by_label("Coding system *").select_option("snomedct")

    # Codelist creation page.
    screenshot_element_with_padding(
        page,
        page.locator("div.container > form"),
        "create-new-codelist-page.png",
        extra={"y": 90, "height": -170},
        full_page=True,
    )

    # Codelist creation page with CSV upload option shown.
    page.locator("summary", has_text="Upload CSV").click()

    screenshot_element_with_padding(
        page,
        page.locator('h2:text("Upload a CSV")').locator("..").locator(".."),
        "create-new-codelist-page-csv.png",
        extra={"x": 30, "width": -60, "y": 30, "height": -60},
    )

    page.get_by_role("button", name="Create").click()

    # Initial codelist builder.
    # Strictly, we should already be able to take a screenshot of the builder.
    # However, without clicking somewhere first, there is seemingly
    # inconsistent behaviour where the height of the image
    # gets truncated some of the time.
    # This is despite using a builder-specific locator.
    # Clicking somewhere after page load seems to make it reliable.
    page.get_by_role("heading", name="Create a codelist").click()

    screenshot_element_with_padding(
        page,
        page.locator("div#codelist-builder-container"),
        "codelist-builder-empty.png",
    )

    page.get_by_role("searchbox", name="Enter a search term…").click()
    page.get_by_role("searchbox", name="Enter a search term…").fill("elbow")

    # Entering a search
    screenshot_element_with_padding(
        page,
        page.locator("div#codelist-builder-container"),
        "codelist-builder-search.png",
    )

    page.get_by_role("button", name="Search", exact=True).click()

    # Validate search result
    page.get_by_role("heading", name='Showing 11 concepts matching "elbow"')

    # Showing a search result
    screenshot_element_with_padding(
        page,
        page.locator("div#codelist-builder-container"),
        "hierarchy-initial.png",
    )

    # Expanding the hierarchy
    codes_to_expand = ["298869002", "298163003", "429554009", "439656005"]
    for code in codes_to_expand:
        concept_locator = page.locator(f"[data-code='{code}']")
        # Iterating through is necessary because for 439656005;
        # there are two rows to expand.
        for row in concept_locator.all():
            row.get_by_role("button", name="⊞").click()

    # Click away to deselect the last expanded code.
    page.get_by_role("heading").first.click()

    screenshot_element_with_padding(
        page,
        page.locator("h5 ~ .builder__container").first.locator(".."),
        "hierarchy-expanded.png",
        extra={"width": -550},
    )

    # Select a concept and exclude a descendant.
    page.locator("[data-code='116309007']").get_by_role("button", name="+").click()
    page.locator("[data-code='298869002']").get_by_role("button", name="−").click()

    # Click away to deselect the last expanded code.
    page.get_by_role("heading").first.click()

    screenshot_element_with_padding(
        page,
        page.locator("h5 ~ .builder__container").first.locator(".."),
        "hierarchy-include-exclude.png",
        extra={"width": -550},
    )

    # Set up a conflict.
    # Include one concept and exclude another, where both have the same child codes.
    page.locator("[data-code='429554009']").get_by_role("button", name="+").click()
    page.locator("[data-code='298163003']").get_by_role("button", name="−").click()

    # Click away to deselect the last expanded code.
    page.get_by_role("heading").first.click()

    screenshot_element_with_padding(
        page,
        page.locator("h5 ~ .builder__container").first.locator(".."),
        "hierarchy-conflict.png",
        extra={"width": -550},
    )

    # Showing "more info" button for a row.
    page.locator("[data-code='439656005']").first.hover()

    screenshot_element_with_padding(
        page,
        page.locator("h5 ~ .builder__container").first.locator(".."),
        "more-info-hover.png",
        extra={"width": -500},
    )

    # Details in "more info"
    # Click the button for the row.
    page.locator("[data-code='439656005'] button.builder__more-info-btn").first.click()

    screenshot_element_with_padding(
        page,
        page.locator("div.modal-content"),
        "more-info-conflict-modal.png",
        extra={"x": 10, "width": -20, "y": 40, "height": -4},
    )

    # Close the "more info" modal.
    page.get_by_role("button", name="Close").click()

    # Concepts found summary.
    screenshot_element_with_padding(
        page,
        page.locator("div.card").first,
        "concepts-filter.png",
    )

    # Exclude the inactive code.
    page.locator("[data-code='156659008']").get_by_role("button", name="−").click()

    # Resolve the conflicting code.
    page.locator("[data-code='429554009']").get_by_role("button", name="−").click()

    # Enter another search.
    page.get_by_role("searchbox", name="Enter a search term…").click()
    page.get_by_role("searchbox", name="Enter a search term…").fill("arthritis")
    page.get_by_role("button", name="Search", exact=True).click()

    # Showing multiple searches.
    screenshot_element_with_padding(
        page,
        page.get_by_role("heading", name="Previous searches").locator(".."),
        "previous-searches.png",
    )

    # Complete the codelist.
    page.locator("[data-code='3723001']").get_by_role("button", name="−").click()

    # Showing save buttons.
    screenshot_element_with_padding(
        page,
        page.locator("div.flex-row > form"),
        "save-buttons.png",
    )

    # Showing version buttons.
    page.get_by_role("button", name="Save for review").click()

    screenshot_element_with_padding(
        page,
        page.locator("div.flex-row > form"),
        "version-buttons.png",
    )

    page.get_by_role("button", name="Create new version").click()

    # The version detail buttons.
    screenshot_element_with_padding(
        page,
        page.locator('h2:text("Versions")').locator(".."),
        "version-list.png",
        full_page=True,
    )

    page.get_by_role("button", name="Save for review").click()

    # Sign off section in metadata.
    page.get_by_role("link", name="Edit metadata").click()
    screenshot_element_with_padding(
        page,
        page.locator("div#signoff-forms"),
        "sign-off.png",
        full_page=True,
        extra={"width": -30},
    )
    page.get_by_role("button", name="Submit").click()

    # The tree with the full list of codes in the codelist
    # Use this tree because we have included and excluded codes.
    page.get_by_role("tab", name="Tree").click()
    screenshot_element_with_padding(
        page,
        page.locator("div.col-md-9").filter(
            has=page.get_by_role("tabpanel", name="Tree")
        ),
        "tree.png",
        extra={"width": -350, "height": -50},
    )

    # Searches tab.
    page.get_by_role("tab", name="Searches").click()
    screenshot_element_with_padding(
        page,
        page.locator("div.col-md-9").filter(
            has=page.get_by_role("tabpanel", name="Searches")
        ),
        "searches-tab.png",
        extra={"width": -20, "height": -50},
    )
