def test_is_member(organisation, organisation_user, user_without_organisation):
    assert organisation_user.is_member(organisation)
    assert not user_without_organisation.is_member(organisation)


def test_is_admin_member(
    organisation, organisation_admin, organisation_user, user_without_organisation
):
    assert organisation_admin.is_admin_member(organisation)
    assert not organisation_user.is_admin_member(organisation)
    assert not user_without_organisation.is_admin_member(organisation)
