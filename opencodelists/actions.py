import structlog
from rest_framework.authtoken.models import Token

from .models import Organisation

logger = structlog.get_logger()


def create_organisation(*, name, url, slug=None):
    org = Organisation.objects.create(name=name, url=url, slug=slug)

    logger.info("Created Organisation", organisation_pk=org.pk)

    return org


def add_user_to_organisation(*, user, organisation, date_joined):
    return user.memberships.create(
        organisation=organisation, date_joined=date_joined, is_admin=False
    )


def remove_user_from_organisation(*, user, organisation):
    return user.get_organisation_membership(organisation).delete()


def make_user_admin_for_organisation(*, user, organisation):
    membership = user.get_organisation_membership(organisation)
    membership.is_admin = True
    membership.save()


def make_user_nonadmin_for_organisation(*, user, organisation):
    membership = user.get_organisation_membership(organisation)
    membership.is_admin = False
    membership.save()


def set_api_token(*, user):
    Token.objects.filter(user=user).delete()
    token, _ = Token.objects.get_or_create(user=user)
    return token
