from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import CreateView

from ..actions import create_user
from ..forms import UserForm
from ..models import User


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
