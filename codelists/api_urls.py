from django.urls import path

from . import api

app_name = "codelists_api"


urlpatterns = [
    path("codelist/<organisation_slug>/", api.codelists, name="codelists"),
]

for subpath, view in [
    ("<codelist_slug>/versions/", api.versions),
]:
    urlpatterns.append(
        path(
            "codelist/<organisation_slug>/" + subpath,
            view,
            name="organisation_" + view.__name__,
        )
    )
    urlpatterns.append(
        path("codelist/user/<username>/" + subpath, view, name="user_" + view.__name__)
    )
