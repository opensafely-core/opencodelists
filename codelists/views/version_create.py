from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.generic import FormView

from .. import actions
from ..forms import CodelistVersionForm
from ..models import Codelist


@method_decorator(login_required, name="dispatch")
class VersionCreate(FormView):
    form_class = CodelistVersionForm
    template_name = "codelists/version_create.html"

    def dispatch(self, request, *args, **kwargs):
        self.codelist = get_object_or_404(
            Codelist.objects.prefetch_related("versions"),
            organisation=self.kwargs["organisation_slug"],
            slug=self.kwargs["codelist_slug"],
        )

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        version = actions.create_version(
            codelist=self.codelist, csv_data=form.cleaned_data["csv_data"]
        )
        return redirect(version)
