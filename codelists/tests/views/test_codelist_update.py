import datetime

from codelists.models import Codelist
from codelists.views.codelist_update import get_owner_choices

from .assertions import (
    assert_get_unauthenticated,
    assert_get_unauthorised,
    assert_post_unauthenticated,
    assert_post_unauthorised,
)
from .helpers import force_login


def test_get_unauthenticated(client, codelist):
    assert_get_unauthenticated(client, codelist.get_update_url())


def test_post_unauthenticated(client, codelist):
    assert_post_unauthenticated(client, codelist.get_update_url())


def test_get_unauthorised(client, codelist):
    assert_get_unauthorised(client, codelist.get_update_url())


def test_post_unauthorised(client, codelist):
    assert_post_unauthorised(client, codelist.get_update_url())


def test_get_success(client, codelist, organisation):
    force_login(codelist, client)
    response = client.get(codelist.get_update_url())

    assert response.status_code == 200

    form = response.context_data["codelist_form"]
    assert form.initial["name"] == codelist.name
    assert form.initial["slug"] == codelist.slug
    assert form.initial["owner"] == f"organisation:{organisation.pk}"
    assert form.initial["description"] == codelist.description
    assert form.initial["methodology"] == codelist.methodology


def test_post_success(client, codelist, organisation_admin):
    signoff_1 = codelist.signoffs.first()
    signoff_2 = codelist.signoffs.last()
    reference_1 = codelist.references.first()
    reference_2 = codelist.references.last()

    assert codelist.references.count() == 2
    assert codelist.signoffs.count() == 2

    data = {
        "name": "Updated name",
        "slug": "updated-slug",
        "owner": f"user:{organisation_admin.username}",
        "description": "Updated description",
        "methodology": "Updated methodology",
        "reference-TOTAL_FORMS": "3",
        "reference-INITIAL_FORMS": "2",
        "reference-MIN_NUM_FORMS": "0",
        "reference-MAX_NUM_FORMS": "1000",
        "reference-0-text": reference_1.text,
        "reference-0-url": reference_1.url,
        "reference-0-id": reference_1.id,
        "reference-0-DELETE": "on",
        "reference-1-text": reference_2.text + " CHANGED",
        "reference-1-url": reference_2.url,
        "reference-1-id": reference_2.id,
        "reference-2-text": "This is a new reference",
        "reference-2-url": "http://example.com",
        "signoff-TOTAL_FORMS": "3",
        "signoff-INITIAL_FORMS": "2",
        "signoff-MIN_NUM_FORMS": "0",
        "signoff-MAX_NUM_FORMS": "1000",
        "signoff-0-user": signoff_1.user.username,
        "signoff-0-date": signoff_1.date,
        "signoff-0-id": signoff_1.id,
        "signoff-0-DELETE": "on",
        "signoff-1-user": signoff_2.user.username,
        "signoff-1-date": signoff_2.date + datetime.timedelta(days=2),
        "signoff-1-id": signoff_2.id,
        "signoff-2-user": organisation_admin.username,
        "signoff-2-date": "2000-01-01",
    }

    force_login(codelist, client)
    response = client.post(codelist.get_update_url(), data=data)

    assert response.status_code == 302
    assert response.url == f"/codelist/user/{organisation_admin.username}/updated-slug/"

    # codelist.refresh_from_db() isn't enough here -- we need to clear the cached
    # current_handle property.
    codelist = Codelist.objects.get(pk=codelist.pk)

    assert codelist.handles.count() == 2
    assert codelist.name == "Updated name"
    assert codelist.slug == "updated-slug"
    assert codelist.owner == organisation_admin

    assert codelist.description == "Updated description"
    assert codelist.methodology == "Updated methodology"

    # we should have still have 2 references but the first should be changed
    # while the second is new.
    assert codelist.references.count() == 2
    assert codelist.references.first().text == reference_2.text + " CHANGED"
    assert codelist.references.last().text == "This is a new reference"

    # we should have still have 2 signoffs but the first should be changed
    # while the second is new.
    assert codelist.signoffs.count() == 2
    assert codelist.signoffs.first().date == signoff_2.date + datetime.timedelta(days=2)
    assert codelist.signoffs.last().user == organisation_admin


def test_post_invalid_duplicate_slug(new_style_codelist, old_style_codelist, client):
    force_login(new_style_codelist, client)
    data = {
        "name": new_style_codelist.name,
        "slug": old_style_codelist.slug,
        "owner": new_style_codelist.owner.owner_identifier,
        "description": "Updated description",
        "methodology": "Updated methodology",
        "reference-TOTAL_FORMS": "0",
        "reference-INITIAL_FORMS": "0",
        "reference-MIN_NUM_FORMS": "0",
        "reference-MAX_NUM_FORMS": "1000",
        "signoff-TOTAL_FORMS": "0",
        "signoff-INITIAL_FORMS": "0",
        "signoff-MIN_NUM_FORMS": "0",
        "signoff-MAX_NUM_FORMS": "1000",
    }

    response = client.post(new_style_codelist.get_update_url(), data=data)
    assert response.context_data["codelist_form"].errors == {"slug": ["Duplicate slug"]}


def test_post_invalid_duplicate_name(new_style_codelist, old_style_codelist, client):
    force_login(new_style_codelist, client)
    data = {
        "name": old_style_codelist.name,
        "slug": new_style_codelist.slug,
        "owner": new_style_codelist.owner.owner_identifier,
        "description": "Updated description",
        "methodology": "Updated methodology",
        "reference-TOTAL_FORMS": "0",
        "reference-INITIAL_FORMS": "0",
        "reference-MIN_NUM_FORMS": "0",
        "reference-MAX_NUM_FORMS": "1000",
        "signoff-TOTAL_FORMS": "0",
        "signoff-INITIAL_FORMS": "0",
        "signoff-MIN_NUM_FORMS": "0",
        "signoff-MAX_NUM_FORMS": "1000",
    }

    response = client.post(new_style_codelist.get_update_url(), data=data)
    assert response.context_data["codelist_form"].errors == {"name": ["Duplicate name"]}


def test_post_invalid_bad_owner(codelist, another_organisation, client):
    force_login(codelist, client)
    data = {
        "name": codelist.name,
        "slug": codelist.slug,
        "owner": another_organisation.owner_identifier,
        "description": "Updated description",
        "methodology": "Updated methodology",
        "reference-TOTAL_FORMS": "0",
        "reference-INITIAL_FORMS": "0",
        "reference-MIN_NUM_FORMS": "0",
        "reference-MAX_NUM_FORMS": "1000",
        "signoff-TOTAL_FORMS": "0",
        "signoff-INITIAL_FORMS": "0",
        "signoff-MIN_NUM_FORMS": "0",
        "signoff-MAX_NUM_FORMS": "1000",
    }

    response = client.post(codelist.get_update_url(), data=data)
    assert (
        response.context_data["codelist_form"]
        .errors["owner"][0]
        .startswith("Select a valid choice")
    )


def test_post_invalid_missing_data(client, codelist):
    signoff_1 = codelist.signoffs.first()
    reference_1 = codelist.references.first()

    # missing signoff-0-date
    data = {
        "description": "This is a test",
        "methodology": "This is how we did it",
        "reference-TOTAL_FORMS": "1",
        "reference-INITIAL_FORMS": "0",
        "reference-MIN_NUM_FORMS": "0",
        "reference-MAX_NUM_FORMS": "1000",
        "reference-0-text": reference_1.text,
        "reference-0-url": reference_1.url,
        "signoff-TOTAL_FORMS": "1",
        "signoff-INITIAL_FORMS": "0",
        "signoff-MIN_NUM_FORMS": "0",
        "signoff-MAX_NUM_FORMS": "1000",
        "signoff-0-user": signoff_1.user.username,
    }

    force_login(codelist, client)
    response = client.post(codelist.get_update_url(), data=data)

    # we're returning an HTML response when there are errors so check we don't
    # receive a redirect code
    assert response.status_code == 200

    # confirm we have errors from the signoff formset
    assert response.context_data["signoff_formset"].errors


def test_post_invalid_with_duplicates(client, codelist):
    signoff_1 = codelist.signoffs.first()
    signoff_2 = codelist.signoffs.last()
    reference_1 = codelist.references.first()
    reference_2 = codelist.references.last()

    data = {
        "description": "This is what we did",
        "methodology": "This is how we did it",
        "reference-TOTAL_FORMS": "2",
        "reference-INITIAL_FORMS": "2",
        "reference-MIN_NUM_FORMS": "0",
        "reference-MAX_NUM_FORMS": "1000",
        "reference-0-url": reference_1.url,
        "reference-0-text": reference_1.text,
        "reference-0-id": reference_1.id,
        "reference-1-url": reference_1.url,  # this duplicates references-0-url
        "reference-1-text": reference_2.text,
        "reference-1-id": reference_2.id,
        "signoff-TOTAL_FORMS": "2",
        "signoff-INITIAL_FORMS": "2",
        "signoff-MIN_NUM_FORMS": "0",
        "signoff-MAX_NUM_FORMS": "1000",
        "signoff-0-user": signoff_1.user.username,
        "signoff-0-date": signoff_1.date,
        "signoff-0-id": signoff_1.id,
        "signoff-1-user": signoff_1.user.username,  # this duplicates signoff-0-user
        "signoff-1-date": signoff_2.date,
        "signoff-1-id": signoff_2.id,
    }

    force_login(codelist, client)
    response = client.post(codelist.get_update_url(), data=data)

    # we're returning an HTML response when there are errors so check we don't
    # receive a redirect code
    assert response.status_code == 200

    # confirm we have errors from the formsets
    assert response.context_data["signoff_formset"].non_form_errors() == [
        "Signoffs must have distinct users."
    ]
    assert response.context_data["reference_formset"].non_form_errors() == [
        "References must have distinct URLs."
    ]


def test_collaborator_can_post(
    client, codelist_with_collaborator, organisation, collaborator
):
    codelist = codelist_with_collaborator
    data = {
        "name": "Updated name",
        "slug": "updated-slug",
        "owner": f"organisation:{organisation.slug}",
        "description": "Updated description",
        "methodology": "Updated methodology",
        "reference-TOTAL_FORMS": "0",
        "reference-INITIAL_FORMS": "0",
        "reference-MIN_NUM_FORMS": "0",
        "reference-MAX_NUM_FORMS": "1000",
        "signoff-TOTAL_FORMS": "0",
        "signoff-INITIAL_FORMS": "0",
        "signoff-MIN_NUM_FORMS": "0",
        "signoff-MAX_NUM_FORMS": "1000",
    }

    client.force_login(collaborator)
    response = client.post(codelist_with_collaborator.get_update_url(), data=data)

    assert response.status_code == 302
    assert response.url == f"/codelist/{organisation.slug}/updated-slug/"

    # codelist.refresh_from_db() isn't enough here -- we need to clear the cached
    # current_handle property.
    codelist = Codelist.objects.get(pk=codelist.pk)

    assert codelist.handles.count() == 2
    assert codelist.name == "Updated name"
    assert codelist.slug == "updated-slug"
    assert codelist.owner == organisation

    assert codelist.description == "Updated description"
    assert codelist.methodology == "Updated methodology"


def test_get_owner_choices(codelist, user, collaborator):
    assert get_owner_choices(codelist, user) == [
        ("user:bob", "Me"),
        ("organisation:test-university", "Test University"),
    ]

    assert get_owner_choices(codelist, collaborator) == [
        ("user:charlie", "Me"),
        ("organisation:test-university", "Test University"),
    ]
