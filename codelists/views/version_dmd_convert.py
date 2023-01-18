from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.utils import IntegrityError
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_POST

from .. import actions
from ..models import Handle
from .decorators import load_version, require_permission


@require_POST
@login_required
@load_version
@require_permission
def version_dmd_convert(request, version):
    try:
        dmd_codelist = actions.convert_bnf_codelist_version_to_dmd(version=version)
    except IntegrityError as e:
        assert "UNIQUE constraint failed" in str(e)
        dmd_codelist = Handle.objects.get(slug=f"{version.codelist.slug}-dmd").codelist
        messages.info(
            request,
            mark_safe(
                f"A <a href='{dmd_codelist.get_absolute_url()}'>dm+d version</a> of this codelist already exists"
            ),
        )
        return redirect(version)
    return redirect(dmd_codelist)
