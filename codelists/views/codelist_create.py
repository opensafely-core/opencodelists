from django.contrib.auth.decorators import login_required
from django.core.exceptions import NON_FIELD_ERRORS
from django.db.utils import IntegrityError
from django.forms import formset_factory
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from opencodelists.models import Organisation

from .. import actions
from ..forms import CodelistCreateForm, ReferenceForm, SignOffForm, data_without_delete


@method_decorator(login_required, name="dispatch")
class CodelistCreate(TemplateView):
    ReferenceFormSet = formset_factory(ReferenceForm, can_delete=True)
    SignOffFormSet = formset_factory(SignOffForm, can_delete=True)
    template_name = "codelists/codelist.html"

    def dispatch(self, request, *args, **kwargs):
        self.organisation = get_object_or_404(
            Organisation, slug=self.kwargs["organisation_slug"]
        )

        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        codelist_form = self.get_form(request.POST, request.FILES)
        reference_formset = self.get_reference_formset(request.POST, request.FILES)
        signoff_formset = self.get_signoff_formset(request.POST, request.FILES)

        all_valid = (
            codelist_form.is_valid()
            and reference_formset.is_valid()
            and signoff_formset.is_valid()
        )

        if all_valid:
            return self.all_valid(codelist_form, reference_formset, signoff_formset)
        else:
            return self.some_invalid(codelist_form, reference_formset, signoff_formset)

    def all_valid(self, codelist_form, reference_formset, signoff_formset):
        # get changed forms so we ignore empty form instances
        references = (
            data_without_delete(f.cleaned_data)
            for f in reference_formset
            if f.has_changed()
        )
        signoffs = (
            data_without_delete(f.cleaned_data)
            for f in signoff_formset
            if f.has_changed()
        )

        name = codelist_form.cleaned_data["name"]

        try:
            codelist = actions.create_codelist(
                organisation=self.organisation,
                name=name,
                coding_system_id=codelist_form.cleaned_data["coding_system_id"],
                description=codelist_form.cleaned_data["description"],
                methodology=codelist_form.cleaned_data["methodology"],
                csv_data=codelist_form.cleaned_data["csv_data"],
                references=references,
                signoffs=signoffs,
            )
        except IntegrityError as e:
            assert "UNIQUE constraint failed" in str(e)
            codelist_form.add_error(
                NON_FIELD_ERRORS,
                f"There is already a codelist in this organisation called {name}",
            )
            return self.some_invalid(codelist_form, reference_formset, signoff_formset)

        return redirect(codelist)

    def some_invalid(self, codelist_form, reference_formset, signoff_formset):
        context = self.get_context_data(
            codelist_form=codelist_form,
            reference_formset=reference_formset,
            signoff_formset=signoff_formset,
        )
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if "codelist_form" not in kwargs:
            context["codelist_form"] = self.get_form()

        if "reference_formset" not in kwargs:
            context["reference_formset"] = self.get_reference_formset()

        if "signoff_formset" not in kwargs:
            context["signoff_formset"] = self.get_signoff_formset()

        return context

    def get_form(self, data=None, files=None):
        return CodelistCreateForm(data, files)

    def get_reference_formset(self, data=None, files=None):
        return self.ReferenceFormSet(data, files, prefix="reference")

    def get_signoff_formset(self, data=None, files=None):
        return self.SignOffFormSet(data, files, prefix="signoff")
