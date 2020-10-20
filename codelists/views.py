from django.contrib.auth.decorators import login_required
from django.core.exceptions import NON_FIELD_ERRORS
from django.db import transaction
from django.db.models import Q
from django.db.utils import IntegrityError
from django.forms import formset_factory
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import FormView, TemplateView

from coding_systems.snomedct.models import Concept as SnomedConcept
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
from .presenters import build_definition_rows


def index(request):
    q = request.GET.get("q")
    if q:
        codelists = Codelist.objects.filter(
            Q(name__contains=q) | Q(description__contains=q)
        )
    else:
        codelists = Codelist.objects.all()

    # For now, we only want to show codelists that were created as part of the
    # OpenSAFELY project.
    codelists = codelists.filter(project_id="opensafely")

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

    def all_valid(self, codelist_form, reference_formset, signoff_formset):
        # get changed forms so we ignore empty form instances
        references = (f.cleaned_data for f in reference_formset if f.has_changed())
        signoffs = (f.cleaned_data for f in signoff_formset if f.has_changed())

        name = codelist_form.cleaned_data["name"]

        try:
            codelist = actions.create_codelist(
                project=self.project,
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
                f"There is already a codelist in this project called {name}",
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

    def get(self, request, *args, **kwargs):
        codelist_form = CodelistUpdateForm(
            {
                "name": self.codelist.name,
                "project": self.codelist.project,
                "coding_system_id": self.codelist.coding_system_id,
                "description": self.codelist.description,
                "methodology": self.codelist.methodology,
            }
        )

        reference_formset = self.get_reference_formset()
        signoff_formset = self.get_signoff_formset()

        context = self.get_context_data(
            codelist_form=codelist_form,
            reference_formset=reference_formset,
            signoff_formset=signoff_formset,
        )
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        codelist_form = CodelistUpdateForm(request.POST, request.FILES)
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
    def all_valid(self, codelist_form, reference_formset, signoff_formset):
        self.save_formset(reference_formset, self.codelist)
        self.save_formset(signoff_formset, self.codelist)

        name = codelist_form.cleaned_data["name"]

        try:
            codelist = actions.update_codelist(
                codelist=self.codelist,
                project=codelist_form.cleaned_data["project"],
                name=codelist_form.cleaned_data["name"],
                coding_system_id=codelist_form.cleaned_data["coding_system_id"],
                description=codelist_form.cleaned_data["description"],
                methodology=codelist_form.cleaned_data["methodology"],
            )
        except IntegrityError as e:
            assert "UNIQUE constraint failed" in str(e)
            codelist_form.add_error(
                NON_FIELD_ERRORS,
                f"There is already a codelist in this project called {name}",
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
            codelist=self.codelist, csv_data=form.cleaned_data["csv_data"]
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

    definition_rows = {}
    child_map = None
    code_to_status = None
    code_to_term = None
    parent_map = None
    tree_tables = None
    if clv.coding_system_id in ["ctv3", "ctv3tpp", "snomedct"]:
        if clv.coding_system_id in ["ctv3", "ctv3tpp"]:
            coding_system = CODING_SYSTEMS["ctv3"]
        else:
            coding_system = CODING_SYSTEMS["snomedct"]

        hierarchy = Hierarchy.from_codes(coding_system, clv.codes)
        parent_map = {p: list(cc) for p, cc in hierarchy.parent_map.items()}
        child_map = {c: list(pp) for c, pp in hierarchy.child_map.items()}
        code_to_term = coding_system.code_to_term(hierarchy.nodes)
        code_to_status = {
            code: "+" if code in clv.codes else "-" for code in hierarchy.nodes
        }
        ancestor_codes = hierarchy.filter_to_ultimate_ancestors(
            set(clv.codes) & hierarchy.nodes
        )
        tree_tables = sorted(
            (type.title(), sorted(codes, key=code_to_term.__getitem__))
            for type, codes in coding_system.codes_by_type(
                ancestor_codes, hierarchy
            ).items()
        )

        definition = Definition.from_codes(set(clv.codes), hierarchy)
        rows = build_definition_rows(coding_system, hierarchy, definition)

        if clv.coding_system_id == "snomedct":
            inactive_codes = SnomedConcept.objects.filter(
                id__in=clv.codes, active=False
            ).values_list("id", flat=True)
            definition_rows = {
                "active": [r for r in rows if r["code"] not in inactive_codes],
                "inactive": [r for r in rows if r["code"] in inactive_codes],
            }
        else:
            definition_rows = {"active": rows, "inactive": []}

    headers, *rows = clv.table

    ctx = {
        "clv": clv,
        "codelist": clv.codelist,
        "versions": clv.codelist.versions.order_by("-version_str"),
        "headers": headers,
        "rows": rows,
        "tree_tables": tree_tables,
        "parent_map": parent_map,
        "child_map": child_map,
        "code_to_term": code_to_term,
        "code_to_status": code_to_status,
        "definition_rows": definition_rows,
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
