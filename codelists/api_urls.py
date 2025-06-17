from django.urls import path

from . import api


app_name = "codelists_api"


urlpatterns = [
    path("codelist/", api.all_codelists, name="all_codelists"),
    path(
        "dmd-mapping/",
        api.dmd_previous_codes_mapping,
        name="dmd_previous_codes_mapping",
    ),
    path("check/", api.codelists_check, name="check_codelists"),
]

for subpath, view in [
    ("", api.codelists),
    ("<slug:codelist_slug>/versions/", api.versions),
]:
    urlpatterns.append(
        path(
            "codelist/<slug:organisation_slug>/" + subpath,
            view,
            name="organisation_" + view.__name__,
        )
    )
    urlpatterns.append(
        path(
            "codelist/user/<slug:username>/" + subpath,
            view,
            name="user_" + view.__name__,
        )
    )
