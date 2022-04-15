from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render

from codelists.models import Codelist
from opencodelists.models import Organisation, User


@login_required
def index(request):
    if not request.user.is_admin:
        raise PermissionDenied

    owner_to_codelists = defaultdict(list)

    for codelist in Codelist.objects.prefetch_related(
        "handles", "handles__organisation", "handles__user", "versions"
    ):
        owner_to_codelists[codelist.owner].append(codelist)

    organisations = []
    users = []

    for owner, codelists in owner_to_codelists.items():
        record = {
            "name": owner.name,
            "codelists": sorted(codelists, key=lambda codelist: codelist.name),
        }
        if isinstance(owner, Organisation):
            organisations.append(record)
        elif isinstance(owner, User):
            users.append(record)
        else:
            assert False

    ctx = {
        "organisations": sorted(organisations, key=lambda record: record["name"]),
        "users": sorted(users, key=lambda record: record["name"]),
    }

    return render(request, "superusers/index.html", ctx)
