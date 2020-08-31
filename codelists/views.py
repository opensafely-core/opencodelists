from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.forms import formset_factory
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import FormView, TemplateView

from opencodelists.models import Project

from . import actions
from .coding_systems import CODING_SYSTEMS
from .definition import Definition
from .forms import (
    CodelistCreateForm,
    CodelistUpdateForm,
    CodelistVersionForm,
    ReferenceForm,
    ReferenceFormSet,
    SignOffForm,
    SignOffFormSet,
)
from .hierarchy import Hierarchy
from .models import Codelist, CodelistVersion
from .presenters import build_html_tree_highlighting_codes


def index(request):
    q = request.GET.get("q")
    if q:
        codelists = Codelist.objects.filter(
            Q(name__contains=q) | Q(description__contains=q)
        )
    else:
        codelists = Codelist.objects.all()
    codelists = codelists.order_by("name")
    ctx = {"codelists": codelists, "q": q}
    return render(request, "codelists/index.html", ctx)


@method_decorator(login_required, name="dispatch")
class CodelistCreate(TemplateView):
    ReferenceFormSet = formset_factory(ReferenceForm)
    SignOffFormSet = formset_factory(SignOffForm)
    template_name = "codelists/codelist.html"

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, slug=self.kwargs["project_slug"])

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

    def all_valid(self, form, reference_formset, signoff_formset):
        # get changed forms so we ignore empty form instances
        references = (f.cleaned_data for f in reference_formset if f.has_changed())
        signoffs = (f.cleaned_data for f in signoff_formset if f.has_changed())

        codelist = actions.create_codelist(
            project=self.project,
            name=form.cleaned_data["name"],
            coding_system_id=form.cleaned_data["coding_system_id"],
            description=form.cleaned_data["description"],
            methodology=form.cleaned_data["methodology"],
            csv_data=form.cleaned_data["csv_data"],
            references=references,
            signoffs=signoffs,
        )

        return redirect(codelist)

    def some_invalid(self, form, reference_formset, signoff_formset):
        context = self.get_context_data(
            codelist_form=form,
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


@method_decorator(login_required, name="dispatch")
class CodelistUpdate(TemplateView):
    template_name = "codelists/codelist.html"

    def dispatch(self, request, *args, **kwargs):
        self.codelist = get_object_or_404(
            Codelist,
            project__slug=self.kwargs["project_slug"],
            slug=self.kwargs["codelist_slug"],
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

    @transaction.atomic
    def all_valid(self, form, reference_formset, signoff_formset):
        self.save_formset(reference_formset, self.codelist)
        self.save_formset(signoff_formset, self.codelist)

        codelist = actions.update_codelist(
            codelist=self.codelist,
            project=form.cleaned_data["project"],
            name=form.cleaned_data["name"],
            coding_system_id=form.cleaned_data["coding_system_id"],
            description=form.cleaned_data["description"],
            methodology=form.cleaned_data["methodology"],
        )

        return redirect(codelist)

    def some_invalid(self, form, reference_formset, signoff_formset):
        context = self.get_context_data(
            codelist_form=form,
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

    def save_formset(self, formset, codelist):
        """
        Save the the given FormSet

        Both our Reference and SignOff FormSets contain forms which are linked
        to a particular Codelist.  We need to set that Codelist on the
        instances generated by the FormSet on `.save()`.
        """
        for instance in formset.save(commit=False):
            instance.codelist = codelist
            instance.save()

        # manually delete the deleted objects since we used .save(commit=False)
        # earlier, as per the docs:
        # https://docs.djangoproject.com/en/3.0/topics/forms/formsets/#can-delete
        for obj in formset.deleted_objects:
            obj.delete()

    def get_form(self, data=None, files=None):
        return CodelistUpdateForm(data, files, instance=self.codelist)

    def get_reference_formset(self, data=None, files=None):
        return ReferenceFormSet(
            data, files, queryset=self.codelist.references.all(), prefix="reference"
        )

    def get_signoff_formset(self, data=None, files=None):
        return SignOffFormSet(
            data, files, queryset=self.codelist.signoffs.all(), prefix="signoff"
        )


def codelist(request, project_slug, codelist_slug):
    codelist = get_object_or_404(
        Codelist.objects.prefetch_related("versions"),
        project=project_slug,
        slug=codelist_slug,
    )

    clv = codelist.versions.order_by("version_str").last()
    return redirect(clv)


@method_decorator(login_required, name="dispatch")
class VersionCreate(FormView):
    form_class = CodelistVersionForm
    template_name = "codelists/version_create.html"

    def dispatch(self, request, *args, **kwargs):
        self.codelist = get_object_or_404(
            Codelist.objects.prefetch_related("versions"),
            project=self.kwargs["project_slug"],
            slug=self.kwargs["codelist_slug"],
        )

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        version = actions.create_version(
            codelist=self.codelist, csv_data=form.cleaned_data["csv_data"],
        )
        return redirect(version)


def version(request, project_slug, codelist_slug, qualified_version_str):
    if qualified_version_str[-6:] == "-draft":
        expect_draft = True
        version_str = qualified_version_str[:-6]
    else:
        expect_draft = False
        version_str = qualified_version_str

    clv = get_object_or_404(
        CodelistVersion.objects.select_related("codelist"),
        codelist__project_id=project_slug,
        codelist__slug=codelist_slug,
        version_str=version_str,
    )

    if expect_draft != clv.is_draft:
        return redirect(clv)

    headers, *rows = clv.table

    html_tree = None

    if clv.coding_system_id in ["ctv3", "ctv3tpp"]:
        coding_system = CODING_SYSTEMS["ctv3"]
        hierarchy = Hierarchy.from_codes(coding_system, clv.codes)
        definition = Definition.from_codes(set(clv.codes), hierarchy)

        html_tree = build_html_tree_highlighting_codes(
            coding_system, hierarchy, definition
        )

    ctx = {
        "clv": clv,
        "codelist": clv.codelist,
        "versions": clv.codelist.versions.order_by("-version_str"),
        "headers": headers,
        "rows": rows,
        "html_tree": html_tree,
    }
    return render(request, "codelists/version.html", ctx)


@require_POST
@login_required
def version_publish(request, project_slug, codelist_slug, qualified_version_str):
    if qualified_version_str[-6:] == "-draft":
        expect_draft = True
        version_str = qualified_version_str[:-6]
    else:
        expect_draft = False
        version_str = qualified_version_str

    version = get_object_or_404(
        CodelistVersion.objects.select_related("codelist"),
        codelist__project_id=project_slug,
        codelist__slug=codelist_slug,
        version_str=version_str,
    )

    if expect_draft != version.is_draft:
        return redirect(version)

    # We want to redirect to the now-published Version after publishing it, but
    # the in-memory instance in this view won't be updated by the .save() call
    # inside the action.  So instead we return the new instance from the action
    # and use that.
    version = actions.publish_version(version=version)

    return redirect(version)


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
            codelist__project_id=self.kwargs["project_slug"],
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


def download(request, project_slug, codelist_slug, qualified_version_str):
    if qualified_version_str[-6:] == "-draft":
        expect_draft = True
        version_str = qualified_version_str[:-6]
    else:
        expect_draft = False
        version_str = qualified_version_str

    clv = get_object_or_404(
        CodelistVersion.objects.select_related("codelist"),
        codelist__project_id=project_slug,
        codelist__slug=codelist_slug,
        version_str=version_str,
    )

    if expect_draft != clv.is_draft:
        raise Http404

    response = HttpResponse(content_type="text/csv")
    content_disposition = 'attachment; filename="{}.csv"'.format(
        clv.download_filename()
    )
    response["Content-Disposition"] = content_disposition
    response.write(clv.csv_data)
    return response
