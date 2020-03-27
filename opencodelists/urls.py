from django.shortcuts import redirect
from django.urls import include, path

urlpatterns = [
    path("", lambda request: redirect("ctv3:index"), name="index"),
    path("ctv3/", include("ctv3.urls")),
]
