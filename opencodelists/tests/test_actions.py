from opencodelists import actions

from .factories import OrganisationFactory, UserFactory


def test_activate_user():
    user = UserFactory(is_active=False)

    user = actions.activate_user(user=user, password="test")

    # user has been activated and has a password set
    assert user.is_active
    assert user.has_usable_password()


def test_create_organisation():
    o = actions.create_organisation(name="Test University", url="https://test.ac.uk")
    assert o.name == "Test University"
    assert o.slug == "test-university"
    assert o.url == "https://test.ac.uk"


def test_create_user():
    user = actions.create_user(
        username="testym",
        name="Testy McTesterson",
        email="test@example.com",
    )

    assert user.username == "testym"
    assert user.name == "Testy McTesterson"
    assert user.email == "test@example.com"


def test_add_user_to_organisation():
    user = UserFactory()
    organisation = OrganisationFactory()

    membership = actions.add_user_to_organisation(
        user=user, organisation=organisation, date_joined="2020-11-12"
    )

    assert membership.user == user
    assert membership.organisation == organisation
    assert str(membership.date_joined) == "2020-11-12"
    assert not membership.is_admin

    assert user.get_organisation_membership(organisation) is not None
    assert organisation.get_user_membership(user) is not None


def test_remove_user_from_organisation():
    user = UserFactory()
    organisation = OrganisationFactory()
    actions.add_user_to_organisation(
        user=user, organisation=organisation, date_joined="2020-11-12"
    )

    actions.remove_user_from_organisation(user=user, organisation=organisation)

    assert user.get_organisation_membership(organisation) is None
    assert organisation.get_user_membership(user) is None


def test_make_user_admin_for_organisation():
    user = UserFactory()
    organisation = OrganisationFactory()
    actions.add_user_to_organisation(
        user=user, organisation=organisation, date_joined="2020-11-12"
    )

    actions.make_user_admin_for_organisation(user=user, organisation=organisation)

    membership = user.get_organisation_membership(organisation)
    assert membership.is_admin


def test_make_user_nonadmin_for_organisation():
    user = UserFactory()
    organisation = OrganisationFactory()
    actions.add_user_to_organisation(
        user=user, organisation=organisation, date_joined="2020-11-12"
    )
    actions.make_user_admin_for_organisation(user=user, organisation=organisation)

    actions.make_user_nonadmin_for_organisation(user=user, organisation=organisation)

    membership = user.get_organisation_membership(organisation)
    assert not membership.is_admin
