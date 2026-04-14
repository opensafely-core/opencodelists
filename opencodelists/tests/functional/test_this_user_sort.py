from datetime import datetime

import pytest
from django.urls import reverse
from django.utils import timezone
from playwright.sync_api import expect

from codelists.actions import cache_hierarchy, create_codelist_from_scratch
from codelists.coding_systems import most_recent_database_alias
from codelists.models import CodelistVersion, Status
from opencodelists.actions import create_organisation
from opencodelists.models import Organisation, User


pytestmark = [
    pytest.mark.functional,
    pytest.mark.django_db(databases=["default", "snomedct_test_20200101"]),
]


def create_draft_codelist(*, owner, author, name, updated_at):
    codelist = create_codelist_from_scratch(
        owner=owner,
        author=author,
        name=name,
        coding_system_id="snomedct",
        coding_system_database_alias=most_recent_database_alias("snomedct"),
    )
    version = codelist.versions.get()
    CodelistVersion.objects.filter(pk=version.pk).update(updated_at=updated_at)


def create_codelist_with_all_statuses(
    *,
    owner,
    author,
    name,
    draft_updated_at,
    under_review_updated_at,
    published_updated_at,
):
    codelist = create_codelist_from_scratch(
        owner=owner,
        author=author,
        name=name,
        coding_system_id="snomedct",
        coding_system_database_alias=most_recent_database_alias("snomedct"),
    )

    under_review = codelist.versions.get(status=Status.DRAFT)
    CodelistVersion.objects.filter(pk=under_review.pk).update(
        status=Status.UNDER_REVIEW,
        updated_at=under_review_updated_at,
    )

    draft = codelist.versions.create(
        author=author,
        status=Status.DRAFT,
        coding_system_release=under_review.coding_system_release,
    )
    cache_hierarchy(version=draft)
    CodelistVersion.objects.filter(pk=draft.pk).update(updated_at=draft_updated_at)

    published = codelist.versions.create(
        author=author,
        status=Status.PUBLISHED,
        coding_system_release=under_review.coding_system_release,
    )
    cache_hierarchy(version=published)
    CodelistVersion.objects.filter(pk=published.pk).update(
        updated_at=published_updated_at
    )


def test_this_user_table_sorting(
    login_context_for_user,
    live_server,
    setup_coding_systems,
):
    username = "ExampleUser"
    primary_org_name = "Zulu Org"
    secondary_org_name = "Yankee Org"

    login_context = login_context_for_user(username, primary_org_name)
    user = User.objects.get(username=username)
    primary_org = Organisation.objects.get(name=primary_org_name)
    secondary_org = create_organisation(
        name=secondary_org_name,
        url="https://example.org/yankee-org",
    )

    create_draft_codelist(
        owner=secondary_org,
        author=user,
        name="Bravo",
        updated_at=timezone.make_aware(datetime(2026, 2, 1, 10, 47)),
    )
    create_draft_codelist(
        owner=primary_org,
        author=user,
        name="Alpha",
        updated_at=timezone.make_aware(datetime(2026, 3, 1, 19, 23)),
    )
    create_draft_codelist(
        owner=user,
        author=user,
        name="charlie",
        updated_at=timezone.make_aware(datetime(2026, 1, 1, 11, 12)),
    )
    create_codelist_with_all_statuses(
        owner=user,
        author=user,
        name="Delta",
        draft_updated_at=timezone.make_aware(datetime(2025, 10, 1, 9, 13)),
        under_review_updated_at=timezone.make_aware(datetime(2025, 11, 15, 10, 12)),
        published_updated_at=timezone.make_aware(datetime(2025, 12, 9, 17, 23)),
    )
    create_draft_codelist(
        owner=user,
        author=user,
        name="echo",
        updated_at=timezone.make_aware(datetime(2026, 4, 1, 11, 22)),
    )

    page = login_context.new_page()
    page.goto(live_server.url + reverse("user", args=[username]))
    table = page.locator("table[data-codelist-search-table]")
    expect(table).to_be_visible()

    name_sort = table.get_by_role("button", name="Name")
    owner_sort = table.get_by_role("button", name="Owner")
    date_sort = table.get_by_role("button", name="Last updated")

    # Default sort by alphabetical
    expect(
        table.locator(
            "tbody:not([data-codelist-search-no-results-body]) > tr:first-child > td:first-child"
        )
    ).to_have_text(["Alpha", "Bravo", "charlie", "Delta", "echo"])

    # Name sort should then be reverse alphabetical
    name_sort.click()
    expect(
        table.locator(
            "tbody:not([data-codelist-search-no-results-body]) > tr:first-child > td:first-child"
        )
    ).to_have_text(["echo", "Delta", "charlie", "Bravo", "Alpha"])

    # Name sort should restore original order
    name_sort.click()
    expect(
        table.locator(
            "tbody:not([data-codelist-search-no-results-body]) > tr:first-child > td:first-child"
        )
    ).to_have_text(["Alpha", "Bravo", "charlie", "Delta", "echo"])

    # Owner sort a->z
    owner_sort.click()
    expect(
        table.locator(
            "tbody:not([data-codelist-search-no-results-body]) > tr:first-child > td:nth-child(2)"
        )
    ).to_have_text(
        ["ExampleUser", "ExampleUser", "ExampleUser", "Yankee Org", "Zulu Org"]
    )

    # Owner sort z->a
    owner_sort.click()
    expect(
        table.locator(
            "tbody:not([data-codelist-search-no-results-body]) > tr:first-child > td:nth-child(2)"
        )
    ).to_have_text(
        ["Zulu Org", "Yankee Org", "ExampleUser", "ExampleUser", "ExampleUser"]
    )

    # Date sort a->z
    date_sort.click()
    expect(
        table.locator(
            "tbody:not([data-codelist-search-no-results-body]) > tr:first-child > td:last-child"
        )
    ).to_have_text(
        [
            "01 Oct 2025 at 09:13",
            "01 Jan 2026 at 11:12",
            "01 Feb 2026 at 10:47",
            "01 Mar 2026 at 19:23",
            "01 Apr 2026 at 11:22",
        ]
    )

    # Date sort z->a
    date_sort.click()
    expect(
        table.locator(
            "tbody:not([data-codelist-search-no-results-body]) > tr:first-child > td:last-child"
        )
    ).to_have_text(
        [
            "01 Apr 2026 at 11:22",
            "01 Mar 2026 at 19:23",
            "01 Feb 2026 at 10:47",
            "01 Jan 2026 at 11:12",
            "01 Oct 2025 at 09:13",
        ]
    )
