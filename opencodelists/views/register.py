from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render

from ..forms import RegisterForm


def register(request):
    if request.user.is_authenticated:
        messages.error(request, "You are already signed in!")
        return redirect("/")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            user = authenticate(
                username=user.username, password=form.cleaned_data["password1"]
            )
            login(request, user)

            return redirect("/")

    else:
        form = RegisterForm()

    context = {"form": form}

    return render(request, "registration/register.html", context)
