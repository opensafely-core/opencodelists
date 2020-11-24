from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from .. import actions
from .decorators import load_version, require_permission


@require_POST
@login_required
@load_version
@require_permission
def version_create(request, version):
    draft = actions.export_to_builder(version=version, owner=request.user)
    return redirect(draft.get_builder_url("draft"))
