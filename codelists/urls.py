from django.urls import path

from . import views

app_name = "codelists"

urlpatterns = [
    path("", views.index, name="index"),
    path("codelist/<project_slug>/<codelist_slug>/", views.codelist, name="codelist"),
    path(
        "codelist/<project_slug>/<codelist_slug>/<version_str>/download.csv",
        views.codelist_download,
        name="codelist_download",
    ),
]
