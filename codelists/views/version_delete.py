from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from .. import actions
from .decorators import load_version, require_permission


@require_POST
@login_required
@load_version
@require_permission
def version_delete(request, version):
    force = "force" in request.POST
    codelist_was_deleted = actions.delete_version(version=version, force=force)
    if codelist_was_deleted:
        return redirect("/")
    else:
        return redirect(version.codelist)
