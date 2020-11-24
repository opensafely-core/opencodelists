from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.core.exceptions import NON_FIELD_ERRORS
from django.db.utils import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views.generic import CreateView

from codelists.actions import create_codelist_from_scratch, create_codelist_with_codes

from .actions import activate_user, create_user
from .forms import CodelistCreateForm, UserForm, UserPasswordForm
from .models import Organisation, User


@login_required
def user_activation_url(request, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        messages.error(request, f"Unknown user '{username}'")
        return redirect("/")

    if user.is_active:
        messages.error(request, f"User '{username}' has already been activated.")
        return redirect("/")

    template_name = "opencodelists/user_activation_url.html"
    url = request.build_absolute_uri(user.get_set_password_url())
    context = {"user": user, "url": url}
    return TemplateResponse(request, template_name, context)


@method_decorator(login_required, name="dispatch")
class UserCreate(CreateView):
    form_class = UserForm
    model = User
    template_name = "opencodelists/user_create.html"

    def form_valid(self, form):
        user = create_user(
            username=form.cleaned_data["username"],
            name=form.cleaned_data["name"],
            email=form.cleaned_data["email"],
        )

        messages.success(self.request, f"Created user '{user.username}'")

        return redirect("user-activation-url", username=user.username)


def user_set_password(request, token):
    # check the signed token from the URL
    try:
        username = User.unsign_username(token)
    except signing.BadSignature:
        messages.error(request, "Invalid User confirmation URL")
        return redirect("/")

    # get the user for which we're setting the password
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        messages.error(request, "Unknown User")
        return redirect("/")

    template_name = "opencodelists/user_set_password.html"

    if request.method == "GET":
        context = {"form": UserPasswordForm()}
        return TemplateResponse(request, template_name, context)

    form = UserPasswordForm(request.POST)

    if not form.is_valid():
        context = {"form": form}
        return TemplateResponse(request, template_name, context)

    user = activate_user(user=user, password=form.cleaned_data["new_password1"])

    # log the, now activated, user in
    user.backend = "django.contrib.auth.backends.ModelBackend"
    login(request, user)

    msg = "You have successfully set your password and activated your account"
    messages.success(request, msg)

    return redirect("/")


def user(request, username):
    user = get_object_or_404(User, username=username)

    # Find all of the codelists with at least one non-draft version.
    codelists = user.codelists.filter(versions__draft_owner__isnull=True).distinct()

    ctx = {
        "user": user,
        "codelists": codelists.order_by("name"),
        "drafts": user.drafts.select_related("codelist").order_by("codelist__name"),
    }

    if user == request.user:
        return render(request, "opencodelists/this_user.html", ctx)
    else:
        return render(request, "opencodelists/that_user.html", ctx)


@login_required
def user_create_codelist(request, username):
    user = get_object_or_404(User, username=username)
    if user != request.user:
        return redirect("/")

    if user.organisations.exists():
        owner_choices = [(f"user:{user.pk}", "Me")]
        for organisation in user.organisations.order_by("name"):
            owner_choices.append((f"organisation:{organisation.pk}", organisation.name))
    else:
        owner_choices = []

    if request.method == "POST":
        return handle_user_create_codelist_post(request, user, owner_choices)
    return handle_user_create_codelist_get(request, user, owner_choices)


def handle_user_create_codelist_get(request, user, owner_choices):
    ctx = {
        "user": user,
        "form": CodelistCreateForm(owner_choices=owner_choices),
    }
    return render(request, "opencodelists/user_create_codelist.html", ctx)


def handle_user_create_codelist_post(request, user, owner_choices):
    form = CodelistCreateForm(request.POST, request.FILES, owner_choices=owner_choices)

    if form.is_valid():
        return handle_user_create_codelist_post_valid(
            request, form, user, owner_choices
        )
    else:
        return handle_user_create_codelist_post_invalid(request, form, user)


def handle_user_create_codelist_post_valid(request, form, user, owner_choices):
    if owner_choices:
        # TODO handle these asserts better
        owner_identifier = form.cleaned_data["owner"]
        assert owner_identifier in [choice[0] for choice in owner_choices]
        if owner_identifier.startswith("user:"):
            owner = get_object_or_404(User, username=owner_identifier[5:])
            assert owner == user
        else:
            assert owner_identifier.startswith("organisation:")
            owner = get_object_or_404(Organisation, slug=owner_identifier[12:])
            assert user.is_member(owner)
    else:
        owner = user

    name = form.cleaned_data["name"]
    coding_system_id = form.cleaned_data["coding_system_id"]
    codes = form.cleaned_data["csv_data"]

    try:
        if codes:
            codelist = create_codelist_with_codes(
                owner=owner, name=name, coding_system_id=coding_system_id, codes=codes
            )
        else:
            codelist = create_codelist_from_scratch(
                owner=owner,
                name=name,
                coding_system_id=coding_system_id,
                draft_owner=user,
            )
    except IntegrityError as e:
        assert "UNIQUE constraint failed" in str(e)
        form.add_error(
            NON_FIELD_ERRORS,
            f"There is already a codelist called {name}",
        )
        return handle_user_create_codelist_post_invalid(request, form, user)

    return redirect(codelist)


def handle_user_create_codelist_post_invalid(request, form, user):
    ctx = {"user": user, "form": form}
    return render(request, "opencodelists/user_create_codelist.html", ctx)
