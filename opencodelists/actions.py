import structlog

from .models import Organisation, Project, User

logger = structlog.get_logger()


def create_organisation(*, name, url, slug=None):
    org = Organisation.objects.create(name=name, url=url, slug=slug)

    logger.info("Created Organisation", organisation_pk=org.pk)

    return org


def create_project(*, name, url, details, organisations):
    p = Project.objects.create(name=name, url=url, details=details)
    p.organisations.set(organisations)

    logger.info("Created Project", project_pk=p.pk)

    return p


def activate_user(*, user, password):
    user.is_active = True
    user.set_password(password)
    user.save()

    logger.info("Activated User", user_pk=user.pk)

    return user


def create_user(*, username, name, email, organisation, is_active=False):
    user = User.objects.create(
        username=username,
        name=name,
        email=email,
        organisation=organisation,
        is_active=is_active,
    )

    logger.info("Created User", user_pk=user.pk)

    return user
