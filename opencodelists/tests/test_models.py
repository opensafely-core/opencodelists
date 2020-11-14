from opencodelists import actions

from .factories import OrganisationFactory, UserFactory


def test_is_member():
    user1 = UserFactory()
    user2 = UserFactory()
    organisation = OrganisationFactory()
    actions.add_user_to_organisation(
        user=user1, organisation=organisation, date_joined="2020-11-12"
    )

    assert user1.is_member(organisation)
    assert not user2.is_member(organisation)


def test_is_admin_member():
    user1 = UserFactory()
    user2 = UserFactory()
    user3 = UserFactory()
    organisation = OrganisationFactory()
    actions.add_user_to_organisation(
        user=user1, organisation=organisation, date_joined="2020-11-12"
    )
    actions.add_user_to_organisation(
        user=user2, organisation=organisation, date_joined="2020-11-12"
    )
    actions.make_user_admin_for_organisation(user=user1, organisation=organisation)

    assert user1.is_admin_member(organisation)
    assert not user2.is_admin_member(organisation)
    assert not user3.is_admin_member(organisation)
