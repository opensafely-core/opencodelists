from django.urls import reverse


def test_organisations_nav(client, user_without_organisation, organisation_user):
    response = client.get("/")
    assert "My organisations" not in response.text

    client.force_login(user_without_organisation)
    response = client.get("/")
    assert "My organisations" not in response.text

    client.force_login(organisation_user)
    response = client.get("/")
    assert "My organisations" in response.text


def test_get_organisations(client, user_without_organisation, organisation_user):
    response = client.get("/organisations/")
    assert response.status_code == 302

    client.force_login(user_without_organisation)
    response = client.get("/organisations/")
    assert response.status_code == 200

    assert not response.context["organisations"]

    client.force_login(organisation_user)
    response = client.get("/organisations/")
    assert list(response.context["organisations"]) == [
        organisation_user.organisations.first()
    ]


def test_get_organisation_members(
    client,
    organisation,
    organisation_admin,
    user_without_organisation,
    organisation_user,
):
    # not logged in
    organisation_members_url = reverse(
        "organisation_members", args=(organisation.slug,)
    )
    response = client.get(organisation_members_url)
    assert response.status_code == 302
    assert response.url == f"{reverse('login')}?next={organisation_members_url}"

    # not a member
    client.force_login(user_without_organisation)
    response = client.get(organisation_members_url)
    assert response.status_code == 302
    assert response.url == reverse("organisations")

    # member
    client.force_login(organisation_user)
    response = client.get(organisation_members_url)
    assert response.status_code == 302
    assert response.url == reverse("organisations")

    # admin
    client.force_login(organisation_admin)
    response = client.get(organisation_members_url)
    assert response.status_code == 200


def test_add_member(
    client,
    organisation,
    organisation_admin,
    organisation_user,
    user_without_organisation,
):
    organisation_members_url = reverse(
        "organisation_members", args=(organisation.slug,)
    )
    client.force_login(organisation_admin)

    response = client.post(
        organisation_members_url, data={"user_idenitfier": "unknown@test.com"}
    )
    assert response.context["form"].is_valid() is False

    response = client.post(
        organisation_members_url, data={"user_idenitfier": organisation_user.email}
    )
    assert response.context["form"].is_valid() is False

    # add user by email address
    assert user_without_organisation.organisations.exists() is False
    response = client.post(
        organisation_members_url,
        data={"user_idenitfier": user_without_organisation.email},
    )
    assert user_without_organisation.organisations.exists() is True
    assert user_without_organisation.organisations.first() == organisation

    # add user by username
    user_without_organisation.memberships.all().delete()
    assert user_without_organisation.organisations.exists() is False
    response = client.post(
        organisation_members_url,
        data={"user_idenitfier": user_without_organisation.username},
    )
    assert user_without_organisation.organisations.exists() is True
    assert user_without_organisation.organisations.first() == organisation
