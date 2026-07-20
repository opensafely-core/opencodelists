import pytest
from django.contrib.admin import AdminSite
from django.test import Client
from django.urls import reverse
from rest_framework.authtoken.models import TokenProxy

from ..admin import OrganisationAdmin, UserAdmin
from ..models import Membership, Organisation, User


@pytest.fixture
def token_admin_client(client: Client, organisation_admin: User) -> Client:
    """Return a test client authenticated with Django Admin access"""

    organisation_admin.is_admin = True
    organisation_admin.save(update_fields=["is_admin"])
    client.force_login(organisation_admin)
    return client


def test_user_admin_organisations(organisation_user, user_without_organisation):
    user_admin = UserAdmin(User, AdminSite())
    org_user = User.objects.get(username=organisation_user.username)
    assert (
        user_admin.get_organisations(org_user)
        == organisation_user.organisations.first().name
    )

    non_org_user = User.objects.get(username=user_without_organisation.username)
    assert user_admin.get_organisations(non_org_user) == ""


def test_organisation_admin_member_count(organisation):
    org_admin = OrganisationAdmin(Organisation, AdminSite())
    assert (
        org_admin.member_count(organisation)
        == Membership.objects.filter(organisation=organisation).count()
    )


def test_token_admin_list_does_not_show_keys(token_admin_client, organisation_user):
    response = token_admin_client.get(reverse("admin:authtoken_tokenproxy_changelist"))
    content = response.content.decode()

    assert response.status_code == 200
    assert organisation_user.username in content
    assert organisation_user.api_token not in content


def test_token_admin_list_allows_adding_tokens(
    token_admin_client, user_with_no_api_token
):
    add_url = reverse("admin:authtoken_tokenproxy_add")
    response = token_admin_client.get(reverse("admin:authtoken_tokenproxy_changelist"))

    assert response.status_code == 200
    assert add_url in response.content.decode()

    response = token_admin_client.post(
        add_url,
        {"user": user_with_no_api_token.pk, "_save": "Save"},
    )

    assert response.status_code == 302
    assert TokenProxy.objects.filter(user=user_with_no_api_token).exists()


def test_token_admin_add_form_only_shows_user(
    token_admin_client,
):
    response = token_admin_client.get(reverse("admin:authtoken_tokenproxy_add"))

    assert response.status_code == 200
    assert tuple(response.context["adminform"].form.fields) == ("user",)


def test_token_admin_view_does_not_allow_changes(token_admin_client, organisation_user):
    response = token_admin_client.get(
        reverse(
            "admin:authtoken_tokenproxy_change",
            args=[organisation_user.pk],
        )
    )

    assert response.status_code == 200
    assert not response.context["has_change_permission"]
    assert b'name="_save"' not in response.content


def test_token_admin_view_allows_deletion(token_admin_client, organisation_user):
    delete_url = reverse(
        "admin:authtoken_tokenproxy_delete",
        args=[organisation_user.pk],
    )
    response = token_admin_client.get(
        reverse(
            "admin:authtoken_tokenproxy_change",
            args=[organisation_user.pk],
        )
    )

    assert response.status_code == 200
    assert response.context["has_delete_permission"]
    assert delete_url in response.content.decode()

    response = token_admin_client.post(delete_url, {"post": "yes"})

    assert response.status_code == 302
    assert not TokenProxy.objects.filter(user=organisation_user).exists()
