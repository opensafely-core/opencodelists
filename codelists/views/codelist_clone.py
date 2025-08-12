from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.decorators.http import require_GET

from .. import actions
from .decorators import load_codelist


@require_GET
@load_codelist
@login_required
def codelist_clone(request, codelist):
    try:
        cloned_codelist = actions.clone_codelist(codelist, request.user)
    except ValueError as e:
        if "Only user-owned codelists can be cloned" in str(e):
            messages.info(request, str(e))
            return redirect(codelist)
        raise e

    return redirect(cloned_codelist)
