from django.shortcuts import get_object_or_404, render

from codelists.models import Status

from ..models import User


def user(request, username):
    user = get_object_or_404(User, username=username)

    # Find all of the codelists owned (in their current version) by this user with at least one published version.
    owned_codelists = user.codelists.filter(
        handles__is_current=True, versions__status=Status.PUBLISHED
    ).distinct()

    # All codelists authored by the user (either themselves or on behalf of an org)
    # AND those with a draft or under review version owned by the user
    codelists_to_display = list(
        set(user.codelists.union(user.authored_for_organisation))
        | {
            version.codelist
            for version in user.drafts.union(user.versions_under_review)
        }
    )

    # For each codelist we return it, and a list of versions including:
    #   - all draft and under review versions
    #   - the latest published version
    all_codelists = [
        {
            "codelist": codelist,
            "versions": list(
                codelist.versions.exclude(status=Status.PUBLISHED).order_by("-id")
            )
            + (
                [codelist.latest_published_version()]
                if codelist.latest_published_version()
                else []
            ),
        }
        for codelist in sorted(codelists_to_display, key=lambda x: (x.name))
        # We can't use a queryset order_by (where versions_under_review/drafts are querysets of CodelistVersion
        # instances), as a codelist can have multiple versions and multiple handles, and this results in duplicates
        # in the returned queryset. See https://code.djangoproject.com/ticket/18165
    ]

    ctx = {
        "user": user,
        "codelists": [
            codelist.latest_published_version()
            for codelist in owned_codelists.order_by("handles__name")
        ],
        # note that name is a property on a codelist, not an attribute, and it comes from the current handle.
        # If we want to order codelists or versions by codelist name, we actually need to order them by handle name.
        "all_codelists": all_codelists,
    }

    if user == request.user:
        return render(request, "opencodelists/this_user.html", ctx)
    else:
        return render(request, "opencodelists/that_user.html", ctx)
