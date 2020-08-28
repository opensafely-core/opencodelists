import structlog

from .models import Organisation, Project

logger = structlog.get_logger()


def create_organisation(*, name, url):
    org = Organisation.objects.create(name=name, url=url)

    logger.info("Created Organisation", organisation_pk=org.pk)

    return org


def create_project(*, name, url, details, organisations):
    p = Project.objects.create(name=name, url=url, details=details)
    p.organisations.set(organisations)

    logger.info("Created Project", project_pk=p.pk)

    return p
