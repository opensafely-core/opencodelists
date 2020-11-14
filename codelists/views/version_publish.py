from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from .. import actions
from ..models import CodelistVersion


@require_POST
@login_required
def version_publish(request, organisation_slug, codelist_slug, qualified_version_str):
    if qualified_version_str[-6:] == "-draft":
        expect_draft = True
        version_str = qualified_version_str[:-6]
    else:
        expect_draft = False
        version_str = qualified_version_str

    version = get_object_or_404(
        CodelistVersion.objects.select_related("codelist"),
        codelist__organisation_id=organisation_slug,
        codelist__slug=codelist_slug,
        version_str=version_str,
    )

    if expect_draft != version.is_draft:
        return redirect(version)

    # We want to redirect to the now-published Version after publishing it, but
    # the in-memory instance in this view won't be updated by the .save() call
    # inside the action.  So instead we return the new instance from the action
    # and use that.
    version = actions.publish_version(version=version)

    return redirect(version)
