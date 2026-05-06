"""Functional tests for CSV upload in user_create_codelist."""

import re

import pytest
from playwright.sync_api import expect

from codelists.models import CodelistVersion
from opencodelists.hash_utils import unhash
from opencodelists.tests.fixtures import SNOMED_FIXTURES_PATH
from opencodelists.tests.functional.test_build_codelist import (
    Navigator,
    setup_playwright_page,
)


pytestmark = pytest.mark.functional


def upload_csv(navigator: Navigator, page):
    """
    Helper method that:
    - navigates to create codelist page
    - fills in codelist name and coding system
    - expands CSV upload details section
    - uploads a CSV file
    - waits for CSV analysis to complete and checks the contents
    """
    # Navigate to create codelist page
    navigator.go_to_create_codelist_page()

    # Fill in codelist name
    page.get_by_role("textbox", name="Codelist name *").fill("CSV Test Codelist")

    # Select SNOMED CT
    page.get_by_label("Coding system *").select_option("snomedct")

    # Expand the CSV upload details section
    csv_details = page.locator("details:has-text('Upload CSV')")
    if not csv_details.get_attribute("open"):
        csv_details.locator("summary").click()

    # Upload CSV
    csv_path = SNOMED_FIXTURES_PATH / "disorder-of-elbow-excl-arthritis.csv"
    page.set_input_files('input[name="csv_data"]', csv_path)

    # Wait for specific detected content to appear
    csv_analysis_section = page.locator("#csv-analysis-section")
    # CSV has header so data starts at row 2
    expect(csv_analysis_section).to_contain_text("1 header row detected")
    expect(csv_analysis_section).to_contain_text("data starts at row 2")
    expect(csv_analysis_section).to_contain_text("6 snomedct codes in column 1")

    # expect two snomed codes in the csv-missing-descendants-table-body element
    missing_descendants_table_body = page.locator("#csv-missing-descendants-table-body")
    expect(missing_descendants_table_body).to_contain_text("202855006")
    expect(missing_descendants_table_body).to_contain_text("439656005")

    csv_descendants_section = page.locator("#csv-descendants-section")
    expect(csv_descendants_section).to_be_visible()
    expect(csv_descendants_section).to_contain_text("2 missing codes")


def create_codelist(page):
    """
    Helper method that:
    - assumes you are on the create codelist page with CSV uploaded
    - clicks the create button
    - waits for navigation to the new draft codelist page
    - returns the created CodelistVersion object
    """
    # Click create codelist
    create_button = page.get_by_role("button", name="Create a draft codelist")
    create_button.click()

    # Wait for navigation away from create page
    page.wait_for_load_state("load", timeout=10000)

    assert "/builder/" in page.url

    # Extract hash from URL to look up the CodelistVersion
    # URL format: /builder/<hash>/
    url_match = re.search(r"/builder/([a-f0-9]+)/?$", page.url)
    assert url_match, f"Could not extract builder hash from URL: {page.url}"
    version_hash = url_match.group(1)

    # Get CodelistVersion from hash
    version_id = unhash(version_hash, "CodelistVersion")
    version = CodelistVersion.objects.get(id=version_id)
    return version


def validate_codelist(version, included_codes, excluded_codes, unresolved_codes):
    """
    Helper method to validate that the codelist version has the expected included,
    excluded, and unresolved codes.
    """
    # Verify included codes
    for code in included_codes:
        code_obj = version.code_objs.get(code=code)
        assert code_obj.status in ["+", "(+)"], f"Code {code} should be included (+)"

    # Verify excluded codes
    for code in excluded_codes:
        code_obj = version.code_objs.get(code=code)
        assert code_obj.status in ["-", "(-)"], f"Code {code} should be excluded (-)"

    # Verify unresolved codes
    for code in unresolved_codes:
        code_obj = version.code_objs.get(code=code)
        assert code_obj.status == "?", f"Code {code} should be unresolved (?)"

    # Verify nothing missed
    all_codes = set(included_codes) | set(excluded_codes) | set(unresolved_codes)
    version_codes = set(version.code_objs.values_list("code", flat=True))
    assert all_codes == version_codes, "Codelist codes do not match expected codes"


@pytest.mark.django_db(
    databases=["default", "snomedct_test_20200101"],
    transaction=True,
)
def test_csv_structure_detection_and_upload(
    non_organisation_login_context, live_server, snomedct_data
):
    page = setup_playwright_page(
        non_organisation_login_context,
        live_server.url,
    )
    navigator = Navigator(page=page, codelist_name="CSV Test Codelist")

    upload_csv(navigator, page)

    # These are the csv codes in the CSV file
    csv_codes = [
        "73583000",
        "429554009",
        "35185008",
        "128133004",
        "239964003",
        "156659008",
    ]
    # These are the two codes not in the CSV but with parents that are in the CSV
    missing_codes = ["202855006", "439656005"]

    version = create_codelist(page)

    # The csv_codes should be included, the missing_codes should be unresolved
    validate_codelist(version, csv_codes, [], missing_codes)

    # Discard draft
    discard_button = page.get_by_role("button", name="Discard")
    discard_button.click()

    # Confirm discard in modal
    confirm_discard_button = page.get_by_role("button", name="Discard draft")
    confirm_discard_button.click()

    # Wait for codelist list page to load
    page.wait_for_load_state("load", timeout=10000)

    # Confirm we are back on the codelist list page and a create codelist button is visible
    create_codelist_button = page.get_by_role("link", name="Create a codelist!")
    expect(create_codelist_button).to_be_visible()

    upload_csv(navigator, page)

    # Check the exclude_child_codes checkbox
    exclude_checkbox = page.locator('input[name="exclude_child_codes"]')
    exclude_checkbox.check()

    # Confirm cells in the table are now struck through
    expect(page.get_by_role("cell", name="202855006")).to_have_css(
        "text-decoration-line", "line-through"
    )
    expect(page.get_by_role("cell", name="439656005")).to_have_css(
        "text-decoration-line", "line-through"
    )

    version = create_codelist(page)

    # The csv_codes should be included, the missing_codes should be excluded
    validate_codelist(version, csv_codes, missing_codes, [])
