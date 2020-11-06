from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "codelists"

urlpatterns = [
    # There was a typo in the codelist names.  If this happens a lot, we could
    # add a "formerly known as" field to Codelist.
    path(
        "codelist/opensafely/permanent-immunosuppresion/",
        RedirectView.as_view(
            url="/codelist/opensafely/permanent-immunosuppression/", permanent=True
        ),
    ),
    path(
        "codelist/opensafely/permanent-immunosuppresion/2020-06-02/download.csv",
        RedirectView.as_view(
            url="/codelist/opensafely/permanent-immunosuppression/2020-06-02/download.csv",
            permanent=True,
        ),
    ),
    path(
        "codelist/opensafely/temporary-immunosuppresion/",
        RedirectView.as_view(
            url="/codelist/opensafely/temporary-immunosuppression/", permanent=True
        ),
    ),
    path(
        "codelist/opensafely/temporary-immunosuppresion/2020-04-24/download.csv",
        RedirectView.as_view(
            url="/codelist/opensafely/temporary-immunosuppression/2020-04-24/download.csv",
            permanent=True,
        ),
    ),
    # ~~~
    path("", views.index, name="index"),
    path("codelist/<project_slug>/", views.index, name="project_index"),
    path(
        "codelist/<project_slug>/add/",
        views.CodelistCreate.as_view(),
        name="create_codelist",
    ),
    path("codelist/<project_slug>/<codelist_slug>/", views.codelist, name="codelist"),
    path(
        "codelist/<project_slug>/<codelist_slug>/edit/",
        views.CodelistUpdate.as_view(),
        name="codelist-edit",
    ),
    path(
        "codelist/<project_slug>/<codelist_slug>/add/",
        views.VersionCreate.as_view(),
        name="version-create",
    ),
    path(
        "codelist/<project_slug>/<codelist_slug>/<qualified_version_str>/",
        views.version,
        name="version-detail",
    ),
    path(
        "codelist/<project_slug>/<codelist_slug>/<qualified_version_str>/publish/",
        views.version_publish,
        name="version-publish",
    ),
    path(
        "codelist/<project_slug>/<codelist_slug>/<qualified_version_str>/update/",
        views.VersionUpdate.as_view(),
        name="version-update",
    ),
    path(
        "codelist/<project_slug>/<codelist_slug>/<qualified_version_str>/download.csv",
        views.download,
        name="download",
    ),
]
