from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from .. import actions
from ..forms import CodelistVersionForm
from ..models import CodelistVersion


@method_decorator(login_required, name="dispatch")
class VersionUpdate(TemplateView):
    """
    Update a given CodelistVersion's CSV data.

    This uses TemplateView instead of UpdateView view since getting a
    CodelistVersion requires a few extra hoops (extra looks params and post
    lookup checks).  Using an UpdateView required enough modifications to the
    method hooks that readability started to suffer.
    """

    template_name = "codelists/version_update.html"

    def dispatch(self, request, *args, **kwargs):
        version_string = self.kwargs["qualified_version_str"]
        if version_string[-6:] == "-draft":
            expect_draft = True
            version_str = version_string[:-6]
        else:
            expect_draft = False
            version_str = version_string

        self.version = get_object_or_404(
            CodelistVersion.objects.select_related("codelist"),
            codelist__organisation_id=self.kwargs["organisation_slug"],
            codelist__slug=self.kwargs["codelist_slug"],
            version_str=version_str,
        )

        if expect_draft != self.version.is_draft:
            return redirect(self.version)

        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = CodelistVersionForm(request.POST, request.FILES)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))

        actions.update_version(
            version=self.version, csv_data=form.cleaned_data["csv_data"]
        )

        return redirect(self.version)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["version"] = self.version

        if "form" not in kwargs:
            context["form"] = CodelistVersionForm()

        return context
