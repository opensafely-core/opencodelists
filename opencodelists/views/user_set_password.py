from django.contrib import messages
from django.contrib.auth import login
from django.core import signing
from django.shortcuts import redirect
from django.template.response import TemplateResponse

from ..actions import activate_user
from ..forms import UserPasswordForm
from ..models import User


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
