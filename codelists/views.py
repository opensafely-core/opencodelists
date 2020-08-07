from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.forms import formset_factory
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from opencodelists.models import Project

from . import actions, tree_utils
from .coding_systems import CODING_SYSTEMS
from .definition import Definition, build_html_definition
from .forms import (
    CodelistForm,
    CodelistVersionForm,
    FormSetHelper,
    ReferenceForm,
    SignOffForm,
)
from .models import Codelist, CodelistVersion


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
class CreateCodelist(TemplateView):
    ReferenceFormSet = formset_factory(ReferenceForm)
    SignOffFormSet = formset_factory(SignOffForm)
    template_name = "codelists/create_codelist.html"

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
        context["helper"] = FormSetHelper()
        context["project"] = self.project

        if "codelist_form" not in kwargs:
            context["codelist_form"] = self.get_form()

        if "reference_formset" not in kwargs:
            context["reference_formset"] = self.get_reference_formset()

        if "signoff_formset" not in kwargs:
            context["signoff_formset"] = self.get_signoff_formset()

        return context

    def get_form(self, data=None, files=None):
        return CodelistForm(data, files)

    def get_reference_formset(self, data=None, files=None):
        return self.ReferenceFormSet(data, files, prefix="reference")

    def get_signoff_formset(self, data=None, files=None):
        return self.SignOffFormSet(data, files, prefix="signoff")


def codelist(request, project_slug, codelist_slug):
    codelist = get_object_or_404(
        Codelist.objects.prefetch_related("versions"),
        project=project_slug,
        slug=codelist_slug,
    )

    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")

        form = CodelistVersionForm(request.POST, request.FILES)
        if form.is_valid():
            clv = actions.create_version(
                codelist=codelist,
                csv_data=form.cleaned_data["csv_data"].read().decode("utf8"),
            )
            return redirect(clv)

    clv = codelist.versions.order_by("version_str").last()
    return redirect(clv)


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

    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")

        update_version_form = CodelistVersionForm(request.POST, request.FILES)
        if update_version_form.is_valid():
            actions.update_version(
                version=clv,
                csv_data=update_version_form.cleaned_data["csv_data"]
                .read()
                .decode("utf8"),
            )
            return redirect(clv)
    else:
        update_version_form = CodelistVersionForm()

    headers, *rows = clv.table

    if clv.coding_system_id in ["ctv3", "ctv3tpp", "snomedct"]:
        if clv.coding_system_id in ["ctv3", "ctv3tpp"]:
            coding_system = CODING_SYSTEMS["ctv3"]
        else:
            coding_system = CODING_SYSTEMS["snomedct"]
        subtree = tree_utils.build_subtree(coding_system, clv.codes)
        definition = Definition.from_codes(clv.codes, subtree)
        html_definition = build_html_definition(coding_system, subtree, definition)
        if clv.coding_system_id in ["ctv3", "ctv3tpp"]:
            html_tree = tree_utils.build_html_tree_highlighting_codes(
                coding_system, subtree, definition
            )
        else:
            html_tree = None
    else:
        html_definition = None
        html_tree = None

    create_version_form = CodelistVersionForm()
    create_version_form.helper.form_action = clv.codelist.get_absolute_url()

    ctx = {
        "clv": clv,
        "codelist": clv.codelist,
        "headers": headers,
        "rows": rows,
        "html_tree": html_tree,
        "html_definition": html_definition,
        "create_version_form": create_version_form,
        "update_version_form": update_version_form,
    }
    return render(request, "codelists/version.html", ctx)


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
