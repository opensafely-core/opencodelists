from functools import singledispatch

from codelists.models import Codelist, CodelistVersion
from opencodelists.models import Organisation, User


@singledispatch
def force_login(instance, client):
    assert False, type(instance)


@force_login.register(User)
def _(user, client):
    client.force_login(user)
    return user


@force_login.register(Organisation)
def _(organisation, client):
    user = organisation.users.order_by("username").first()
    return force_login(user, client)


@force_login.register(Codelist)
def _(codelist, client):
    if codelist.user:
        return force_login(codelist.user, client)
    else:
        return force_login(codelist.organisation, client)


@force_login.register(CodelistVersion)
def _(version, client):
    return force_login(version.codelist, client)
