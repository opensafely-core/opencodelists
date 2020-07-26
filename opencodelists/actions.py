from .models import Organisation, Project


def create_organisation(*, name, url):
    return Organisation.objects.create(name=name, url=url)


def create_project(*, name, url, details, organisations):
    p = Project.objects.create(name=name, url=url, details=details)
    p.organisations.set(organisations)
    return p
