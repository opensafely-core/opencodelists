from django.shortcuts import redirect
from django.urls import include, path

urlpatterns = [
    path("", lambda request: redirect("coding_systems.ctv3:index"), name="index"),
    path("ctv3/", include("coding_systems.ctv3.urls")),
]
