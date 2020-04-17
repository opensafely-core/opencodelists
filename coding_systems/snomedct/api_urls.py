from django.urls import path

from . import api

app_name = "snomedct-api"

urlpatterns = [
    path("concepts/", api.concepts, name="concepts"),
    path("search/", api.search, name="search"),
]
