from django.shortcuts import get_object_or_404, render

from codelists.models import Status

from ..models import User


def user(request, username):
    user = get_object_or_404(User, username=username)

    # Find all of the codelists owned (in their current version) by this user with at least one published version.
    owned_codelists = user.codelists.filter(
        handles__is_current=True, versions__status=Status.PUBLISHED
    ).distinct()

    # Find all of the codelists authored (but not owned) by this user with at least one published version.
    authored_for_organisation = user.authored_for_organisation.distinct().difference(
        owned_codelists
    )
    ctx = {
        "user": user,
        "codelists": owned_codelists.order_by("handles__name"),
        # note that name is a property on a codelist, not an attribute, and it comes from the current handle.
        # If we want to order codelists or versions by codelist name, we actually need to order them by handle name.
        # We can't use a queryset order_by in the following cases (where versions_under_review/drafts are querysets of
        # CodelistVersion instances), as a codelist can have multiple versions and multiple handles,
        # and this results in duplicates in the returned queryset.
        # See https://code.djangoproject.com/ticket/18165
        # Sort by organisation then name
        "authored_for_organisation": sorted(
            authored_for_organisation, key=lambda x: (x.owner.name, x.name)
        ),
        "under_review": sorted(
            user.versions_under_review.select_related("codelist"),
            key=lambda x: x.codelist.name,
        ),
        "drafts": sorted(
            user.drafts.select_related("codelist"), key=lambda x: x.codelist.name
        ),
    }

    if user == request.user:
        return render(request, "opencodelists/this_user.html", ctx)
    else:
        return render(request, "opencodelists/that_user.html", ctx)
