from opencodelists import actions


def test_activate_user(inactive_user):
    actions.activate_user(user=inactive_user, password="test")

    # user has been activated and has a password set
    assert inactive_user.is_active
    assert inactive_user.has_usable_password()


def test_create_organisation():
    o = actions.create_organisation(
        name="Another Test University", url="https://another-test.ac.uk"
    )
    assert o.name == "Another Test University"
    assert o.slug == "another-test-university"
    assert o.url == "https://another-test.ac.uk"


def test_create_user():
    user = actions.create_user(
        username="testym",
        name="Testy McTesterson",
        email="test@example.com",
    )

    assert user.username == "testym"
    assert user.name == "Testy McTesterson"
    assert user.email == "test@example.com"


def test_add_user_to_organisation(organisation, user_without_organisation):
    user = user_without_organisation

    membership = actions.add_user_to_organisation(
        user=user, organisation=organisation, date_joined="2020-11-12"
    )

    assert membership.user == user
    assert membership.organisation == organisation
    assert str(membership.date_joined) == "2020-11-12"
    assert not membership.is_admin

    assert user.get_organisation_membership(organisation) is not None
    assert organisation.get_user_membership(user) is not None


def test_remove_user_from_organisation(organisation, organisation_user):
    user = organisation_user

    actions.remove_user_from_organisation(user=user, organisation=organisation)

    assert user.get_organisation_membership(organisation) is None
    assert organisation.get_user_membership(user) is None


def test_make_user_admin_for_organisation(organisation, organisation_user):
    user = organisation_user

    actions.make_user_admin_for_organisation(user=user, organisation=organisation)

    membership = user.get_organisation_membership(organisation)
    assert membership.is_admin


def test_make_user_nonadmin_for_organisation(organisation, organisation_admin):
    user = organisation_admin

    actions.make_user_nonadmin_for_organisation(user=user, organisation=organisation)

    membership = user.get_organisation_membership(organisation)
    assert not membership.is_admin


def test_set_api_token(organisation_admin):
    assert organisation_admin.api_token is None
    actions.set_api_token(user=organisation_admin)
    assert organisation_admin.api_token is not None
    old_token = organisation_admin.api_token
    actions.set_api_token(user=organisation_admin)
    assert organisation_admin.api_token is not None
    assert organisation_admin.api_token != old_token
