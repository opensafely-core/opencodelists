import csv
from dataclasses import dataclass
from enum import Enum, StrEnum, auto
from functools import cached_property

import pytest
from playwright.sync_api import expect


pytestmark = pytest.mark.functional


class ConceptState(Enum):
    """Represents states as a results of user interaction
    in the builder for individual concepts."""

    INCLUDED = auto()
    EXCLUDED = auto()


@dataclass(frozen=True)
class ConceptSelection:
    """Represents an intended concept selection on the codelist builder page."""

    code: str
    term: str

    # We're not currently testing collapsing of selections.
    # That may warrant a NOT_SELECTED ConceptState.
    to_expand: bool

    state: ConceptState


@dataclass(frozen=True)
class Search:
    """Represents a search query input."""

    query: str
    # is_code is True if the search is a code, and not a term.
    is_code: bool


@dataclass(frozen=True)
class SearchAction:
    """Represents the action of searching for a term or code, and applying a
    series of ConceptSelections."""

    search: Search
    concept_selections: list[ConceptSelection]

    def search_in_codelist_builder(self, page):
        """Takes a Playwright page that's navigated to the codelist builder,
        and str search.
        Performs the provided search on the codelist builder page."""

        if self.search.is_code:
            page.get_by_role("radio", name="Code").click()

        page.get_by_role("searchbox").click()
        page.get_by_role("searchbox").fill(self.search.query)
        page.get_by_role("button", name="Search", exact=True).click()

    def handle_concept_selections(self, page):
        """Takes a Playwright page that's navigated to the codelist builder,
        and a SearchAction.
        Perform the appropriate ConceptSelection actions belonging to that
        SearchAction on the Playwright page."""

        for concept_selection in self.concept_selections:
            concept_locator = page.locator(f"[data-code='{concept_selection.code}']")

            if concept_selection.to_expand:
                concept_locator.get_by_role("button", name="⊞").click()

            match concept_selection.state:
                case ConceptState.INCLUDED:
                    button_icon = "+"
                case ConceptState.EXCLUDED:
                    button_icon = "−"
                case _:
                    # Guard against adding another ConceptState value.
                    assert False

            concept_locator.get_by_role("button", name=button_icon).click()


@dataclass(frozen=True)
class SearchActions:
    """Represents a series of SearchActions."""

    items: list[SearchAction]

    @cached_property
    def expected_codelist_table(self):
        """Returns a dictionary mapping codes to terms.

        Later ConceptSelections intentionally take precedence."""
        # Caching this is based on frozen=True.
        # If this changes, we may have to recompute the value.
        assert self.__dataclass_params__.frozen

        all_concept_selections = []
        for search_action in self.items:
            all_concept_selections.extend(search_action.concept_selections)

        return {
            concept_selection.code: concept_selection.term
            for concept_selection in all_concept_selections
            if concept_selection.state == ConceptState.INCLUDED
        }

    def apply(self, page):
        """Applies each SearchAction in turn: searching and selecting concepts."""
        for search_action in self.items:
            search_action.search_in_codelist_builder(page)
            expect(page.get_by_role("button", name="Save for review")).to_be_disabled()
            search_action.handle_concept_selections(page)


class CodelistHeading(StrEnum):
    """Represents the heading for a codelist on the My Codelists page."""

    USER_OWNED = "Your published codelists"
    ORGANISATION_OWNED = "Your organisation codelists"
    REVIEW = "Your codelists under review"
    DRAFT = "Your draft codelists"


def setup_playwright_page(login_context, url):
    """Takes a login context, and returns a Playwright page."""

    page = login_context.new_page()
    page.goto(url)
    expect(page.get_by_role("button", name="My account")).to_be_visible()
    return page


def create_codelist(page, coding_system, name):
    """Takes a Playwright page, navigates to the codelist creation page
    and, for supported coding systems, fills in the form to create a new codelist."""

    if coding_system not in ["bnf", "snomedct"]:
        # For example:
        # * database fixtures may need properly enabling
        # * we need to implement proper search-by-term/code switching
        #   for ICD10 where we can't distinguish between terms and codes
        #   by looking at the search string (see search_in_codelist_builder())
        assert False, "Coding system {coding_system} not yet supported by the tests"

    page.get_by_role("link", name="My codelists").click()
    page.get_by_role("link", name="Create a codelist!").click()

    page.get_by_role("textbox", name="Codelist name *").fill(name)
    page.get_by_label("Coding system *").select_option(coding_system)
    page.get_by_role("button", name="Create").click()


def save_codelist_for_review(page):
    """Takes a Playwright page on a codelist builder page,
    with a completed codelist, and saves the codelist for review."""

    save_for_review_link = page.get_by_role("button", name="Save for review")
    expect(save_for_review_link).to_be_enabled()
    save_for_review_link.click()


def validate_codelist_exists_on_site(page, codelist_name, codelist_heading):
    """Takes a Playwright page, a codelist name, and CodelistHeading to match
    and validates that the codelist name exists under that heading.

    It does not currently go for an exact match because organisation users get
    "owned by organisation" appended to the codelist name.

    We could improve this matching in future."""

    page.get_by_role("link", name="My codelists").click()
    codelist_link = page.get_by_role("link", name=codelist_name)
    expect(codelist_link).to_be_visible()
    expect(
        page.get_by_role("link", name=codelist_name)
        .locator("xpath=preceding::h4")
        .nth(-1)
    ).to_have_text(codelist_heading.value)


def verify_review_codelist_codes(page, codelist_name, search_actions):
    """Takes a page, codelist name, a list of ConceptSelections,
    and the text used for a search, and verifies the expected codelist codes
    are present on the full list tab.

    It does not yet, but will validate the searches tab.

    It is limited to verifying the result of a codelist selection
    following a single search for now."""
    page.get_by_role("link", name="My codelists").click()
    page.get_by_role("link", name=codelist_name).click()

    page.get_by_role("tab", name="Full list").click()
    codelist_table_rows = page.locator("div#full-list").locator("table tr")
    codelist_table_as_dict = {}

    # Collate the codes; skipping the table header row.
    for row in codelist_table_rows.all()[1:]:
        code = row.locator("td").nth(0).text_content()
        term = row.locator("td").nth(1).text_content()
        codelist_table_as_dict[code] = term

    assert codelist_table_as_dict == search_actions.expected_codelist_table


def publish_codelist(page, codelist_name):
    """Take a Playwright page and codelist name,
    and publish the codelist.

    Requires that the codelist has been saved for review
    and is ready to be published."""

    page.get_by_role("link", name="My codelists").click()
    page.get_by_role("link", name=codelist_name).click()

    page.get_by_role("button", name="Publish version").click()
    page.get_by_role("button", name="Publish", exact=True).click()


def verify_codelist_csv(page, codelist_name, search_actions):
    """Take a Playwright page, codelist name, and expected codelist table,
    and verifies the codelist CSV against the expected codelist table.

    Requires that the codelist has been published."""

    page.get_by_role("link", name="My codelists").click()
    page.get_by_role("link", name=codelist_name).click()

    with page.expect_download() as download_info:
        page.get_by_role("button", name="Download CSV").click()

    codelist_table_from_csv = {}

    with open(download_info.value.path()) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            code = row["code"]
            term = row["term"]
            codelist_table_from_csv[code] = term

    assert codelist_table_from_csv == search_actions.expected_codelist_table


@pytest.mark.parametrize(
    # Test by searching with term, and then by searching with code.
    "search",
    [Search(query="arthritis", is_code=False), Search(query="3723001", is_code=True)],
)
@pytest.mark.parametrize(
    # Test with a non-organisation user login, and then organisation user login.
    "login_context_fixture_name",
    ["non_organisation_login_context", "organisation_login_context"],
)
@pytest.mark.django_db(
    databases=[
        "default",
        "snomedct_test_20200101",
    ],
    transaction=True,
)
def test_build_snomedct_codelist_single_search(
    login_context_fixture_name, search, request, live_server, snomedct_data
):
    page = setup_playwright_page(
        login_context=request.getfixturevalue(login_context_fixture_name),
        url=live_server.url,
    )

    coding_system = "snomedct"
    codelist_name = "Test"
    create_codelist(page, coding_system, codelist_name)

    search_actions = SearchActions(
        items=[
            SearchAction(
                search=search,
                concept_selections=[
                    ConceptSelection(
                        code="3723001",
                        term="Arthritis",
                        to_expand=False,
                        state=ConceptState.INCLUDED,
                    ),
                    ConceptSelection(
                        code="439656005",
                        term="Arthritis of elbow",
                        to_expand=True,
                        state=ConceptState.EXCLUDED,
                    ),
                    ConceptSelection(
                        code="202855006",
                        term="Lateral epicondylitis",
                        to_expand=False,
                        state=ConceptState.EXCLUDED,
                    ),
                ],
            ),
        ],
    )
    # This test only has one action,
    # but writing in this format for consistency of the tests.
    search_actions.apply(page)

    save_codelist_for_review(page)
    validate_codelist_exists_on_site(page, codelist_name, CodelistHeading.REVIEW)

    verify_review_codelist_codes(page, codelist_name, search_actions)

    publish_codelist(page, codelist_name)

    validate_codelist_exists_on_site(page, codelist_name, CodelistHeading.USER_OWNED)

    verify_codelist_csv(page, codelist_name, search_actions)


@pytest.mark.parametrize(
    # Test by searching with term, and then by searching with code.
    "search",
    [Search(query="asthma", is_code=False), Search(query="0301012A0AA", is_code=True)],
)
@pytest.mark.parametrize(
    # Test with a non-organisation user login, and then organisation user login.
    "login_context_fixture_name",
    ["non_organisation_login_context", "organisation_login_context"],
)
@pytest.mark.django_db(
    databases=[
        "default",
        "bnf_test_20200101",
    ],
    transaction=True,
)
def test_build_bnf_codelist_single_search(
    login_context_fixture_name, search, request, live_server, bnf_data
):
    page = setup_playwright_page(
        login_context=request.getfixturevalue(login_context_fixture_name),
        url=live_server.url,
    )

    coding_system = "bnf"
    codelist_name = "Test"
    create_codelist(page, coding_system, codelist_name)

    search_actions = SearchActions(
        items=[
            SearchAction(
                search=search,
                concept_selections=[
                    ConceptSelection(
                        code="0301012A0AA",
                        term="Adrenaline (Asthma)",
                        to_expand=False,
                        state=ConceptState.INCLUDED,
                    ),
                    ConceptSelection(
                        code="0301012A0AAABAB",
                        term="Adrenaline (base) 220micrograms/dose inhaler",
                        to_expand=False,
                        state=ConceptState.EXCLUDED,
                    ),
                    ConceptSelection(
                        code="0301012A0AAACAC",
                        term="Adrenaline (base) 220micrograms/dose inhaler refill",
                        to_expand=False,
                        state=ConceptState.EXCLUDED,
                    ),
                ],
            ),
        ],
    )
    # This test only has one action,
    # but writing in this format for consistency of the tests.
    search_actions.apply(page)

    save_codelist_for_review(page)
    validate_codelist_exists_on_site(page, codelist_name, CodelistHeading.REVIEW)

    verify_review_codelist_codes(
        page,
        codelist_name,
        search_actions,
    )

    publish_codelist(page, codelist_name)

    validate_codelist_exists_on_site(page, codelist_name, CodelistHeading.USER_OWNED)

    verify_codelist_csv(page, codelist_name, search_actions)


@pytest.mark.parametrize(
    # Test with a non-organisation user login, and then organisation user login.
    "login_context_fixture_name",
    ["non_organisation_login_context", "organisation_login_context"],
)
@pytest.mark.django_db(
    databases=[
        "default",
        "snomedct_test_20200101",
    ],
    transaction=True,
)
def test_build_snomedct_codelist_two_searches_no_selections(
    login_context_fixture_name,
    request,
    live_server,
    snomedct_data,
):
    page = setup_playwright_page(
        login_context=request.getfixturevalue(login_context_fixture_name),
        url=live_server.url,
    )

    coding_system = "snomedct"
    codelist_name = "Test"
    create_codelist(page, coding_system, codelist_name)

    search_actions = SearchActions(
        items=[
            SearchAction(
                search=Search(
                    query="arthritis",
                    is_code=False,
                ),
                concept_selections=[],
            ),
            SearchAction(
                search=Search(
                    query="tennis",
                    is_code=False,
                ),
                concept_selections=[],
            ),
        ],
    )
    # This test has no concept selections,
    # but writing in this format for consistency of the tests.
    search_actions.apply(page)

    validate_codelist_exists_on_site(page, codelist_name, CodelistHeading.DRAFT)

    # No content to verify for an empty draft.


@pytest.mark.parametrize(
    # Test with a non-organisation user login, and then organisation user login.
    "login_context_fixture_name",
    ["non_organisation_login_context", "organisation_login_context"],
)
@pytest.mark.django_db(
    databases=[
        "default",
        "snomedct_test_20200101",
    ],
    transaction=True,
)
def test_build_snomedct_codelist_two_searches(
    login_context_fixture_name,
    request,
    live_server,
    snomedct_data,
):
    page = setup_playwright_page(
        login_context=request.getfixturevalue(login_context_fixture_name),
        url=live_server.url,
    )

    coding_system = "snomedct"
    codelist_name = "Test"
    create_codelist(page, coding_system, codelist_name)

    search_actions = SearchActions(
        items=[
            SearchAction(
                search=Search(
                    query="arthritis",
                    is_code=False,
                ),
                concept_selections=[
                    ConceptSelection(
                        code="3723001",
                        term="Arthritis",
                        to_expand=False,
                        state=ConceptState.INCLUDED,
                    ),
                    ConceptSelection(
                        code="439656005",
                        term="Arthritis of elbow",
                        to_expand=True,
                        state=ConceptState.EXCLUDED,
                    ),
                    ConceptSelection(
                        code="202855006",
                        term="Lateral epicondylitis",
                        to_expand=False,
                        state=ConceptState.EXCLUDED,
                    ),
                ],
            ),
            SearchAction(
                search=Search(
                    query="tennis",
                    is_code=False,
                ),
                concept_selections=[
                    ConceptSelection(
                        code="202855006",
                        term="Lateral epicondylitis",
                        to_expand=False,
                        state=ConceptState.EXCLUDED,
                    ),
                    ConceptSelection(
                        code="238484001",
                        term="Tennis toe",
                        to_expand=False,
                        state=ConceptState.EXCLUDED,
                    ),
                    # This is an "inactive" code,
                    # so maybe not a good "real-world" example.
                    ConceptSelection(
                        code="156659008",
                        term="(Epicondylitis &/or tennis elbow) or (golfers' elbow)",
                        to_expand=False,
                        state=ConceptState.INCLUDED,
                    ),
                ],
            ),
        ],
    )
    search_actions.apply(page)

    save_codelist_for_review(page)
    validate_codelist_exists_on_site(page, codelist_name, CodelistHeading.REVIEW)

    verify_review_codelist_codes(page, codelist_name, search_actions)

    publish_codelist(page, codelist_name)

    validate_codelist_exists_on_site(page, codelist_name, CodelistHeading.USER_OWNED)

    verify_codelist_csv(page, codelist_name, search_actions)
