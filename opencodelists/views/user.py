from django.shortcuts import get_object_or_404, render

from codelists.models import Status

from ..models import User


def user(request, username):
    user = get_object_or_404(User, username=username)

    # Find all of the codelists with at least one non-draft version.
    codelists = user.codelists.filter(versions__draft_owner__isnull=True).distinct()

    ctx = {
        "user": user,
        "codelists": codelists.order_by("handles__name"),
        "under_review": user.drafts.select_related("codelist")
        .filter(status=Status.UNDER_REVIEW)
        .order_by("codelist__handles__name"),
        "drafts": user.drafts.select_related("codelist")
        .filter(status=Status.DRAFT)
        .order_by("codelist__handles__name"),
    }

    if user == request.user:
        return render(request, "opencodelists/this_user.html", ctx)
    else:
        return render(request, "opencodelists/that_user.html", ctx)
