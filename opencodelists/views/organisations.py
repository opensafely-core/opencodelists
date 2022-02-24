from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from ..actions import add_user_to_organisation
from ..forms import MembershipCreateForm
from .decorators import load_organisation, require_admin_permission


@login_required
def organisations(request):
    """List organisations that the user is a member of"""
    ctx = {
        "organisations": request.user.organisations.all(),
        "admin_organisations": request.user.memberships.filter(
            is_admin=True
        ).values_list("organisation", flat=True),
    }
    return render(request, "opencodelists/user_organisations.html", ctx)


@login_required
@load_organisation
@require_admin_permission
def organisation_members(request, organisation):
    """List members of an organisation and allow admin user to add new users"""
    organisation_users = organisation.users.all().order_by("name")
    ctx = {
        "organisation": organisation,
        "organisation_members": organisation_users,
        "form": MembershipCreateForm(organisation=organisation),
    }

    if request.method == "POST":
        form = MembershipCreateForm(request.POST, organisation=organisation)
        if form.is_valid():
            add_user_to_organisation(
                user=form.user, organisation=organisation, date_joined=datetime.today()
            )
            ctx.update(
                {
                    "just_added": form.user,
                    "organisation_members": organisation_users.exclude(
                        username=form.user.username
                    ),
                }
            )
        else:
            ctx["form"] = form

    return render(request, "opencodelists/organisation_members.html", ctx)
