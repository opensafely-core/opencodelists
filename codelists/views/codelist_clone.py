from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.decorators.http import require_GET

from .. import actions
from .decorators import load_codelist


@require_GET
@load_codelist
@login_required
def codelist_clone(request, codelist):
    cloned_codelist = actions.clone_codelist(codelist, request.user)
    return redirect(cloned_codelist)
