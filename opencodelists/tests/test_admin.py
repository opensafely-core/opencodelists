from django.contrib.admin import AdminSite

from ..admin import OrganisationAdmin, UserAdmin
from ..models import Membership, Organisation, User


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
