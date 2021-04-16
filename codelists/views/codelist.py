from django.contrib import messages
from django.shortcuts import redirect

from .decorators import load_codelist


@load_codelist
def codelist(request, codelist):
    clv = codelist.latest_version()
    if clv is not None:
        return redirect(clv)
    else:
        messages.add_message(
            request, messages.INFO, "This codelist has not been published"
        )
        return redirect("/")
