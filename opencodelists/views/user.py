from django.shortcuts import get_object_or_404, render

from ..models import User


def user(request, username):
    user = get_object_or_404(User, username=username)

    # Find all of the codelists with at least one non-draft version.
    codelists = user.codelists.filter(versions__draft_owner__isnull=True).distinct()

    ctx = {
        "user": user,
        "codelists": codelists.order_by("handles__name"),
        "drafts": user.drafts.select_related("codelist").order_by(
            "codelist__handles__name"
        ),
    }

    if user == request.user:
        return render(request, "opencodelists/this_user.html", ctx)
    else:
        return render(request, "opencodelists/that_user.html", ctx)
