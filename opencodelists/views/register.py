from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render

from ..forms import RegisterForm


def register(request):
    if request.user.is_authenticated:
        messages.error(request, "You are already signed in!")
        return redirect("/")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                user = authenticate(
                    username=user.username, password=form.cleaned_data["password1"]
                )
                login(request, user)

                return redirect("/")
            except ValidationError as e:
                # In theory this shouldn't happen because a duplicate username
                # causes form.is_valid() to return False. But we've seen this
                # error happen once in production - possibly due to some race
                # condition. So we handle it here.
                if (
                    hasattr(e, "messages")
                    and "A user with this username already exists." in e.messages
                ):
                    form.add_error(
                        "username", "A user with this username already exists."
                    )
                else:
                    raise

    else:
        form = RegisterForm()

    context = {"form": form}

    return render(request, "registration/register.html", context)
