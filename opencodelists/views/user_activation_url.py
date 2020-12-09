from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.template.response import TemplateResponse

from ..models import User


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
