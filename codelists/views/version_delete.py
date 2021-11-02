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
    codelist_was_deleted = actions.delete_version(version=version)
    if codelist_was_deleted:
        return redirect("/")
    else:
        return redirect(version.codelist)
