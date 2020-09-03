from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views.generic import CreateView

from .actions import activate_user, create_user
from .forms import UserForm, UserPasswordForm
from .models import Project, User


def project(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    ctx = {"project": project}
    return render(request, "opencodelists/project.html", ctx)


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
            organisation=form.cleaned_data["organisation"],
        )

        messages.success(self.request, f"Created user '{user.username}'")

        return redirect("/")


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
