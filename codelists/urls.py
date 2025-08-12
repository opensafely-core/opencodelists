from django.urls import path
from django.views.generic import RedirectView

from . import views
from .models import Status


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
    path("codelist/<slug:organisation_slug>/", views.index, name="organisation_index"),
    path(
        "codelist/<slug:organisation_slug>/under-review/",
        views.index,
        {"status": Status.UNDER_REVIEW},
        name="organisation_under_review_index",
    ),
]

for subpath, view in [
    ("add/", views.codelist_create),
    ("<slug:codelist_slug>/", views.codelist),
    ("<slug:codelist_slug>/edit/", views.codelist_update),
    ("<slug:codelist_slug>/clone/", views.codelist_clone),
    ("<slug:codelist_slug>/upload-version/", views.version_upload),
    ("<slug:codelist_slug>/<str:tag_or_hash>/", views.version),
    (
        "<slug:codelist_slug>/<str:tag_or_hash>/create-new-version/",
        views.version_create,
    ),
    ("<slug:codelist_slug>/<str:tag_or_hash>/publish/", views.version_publish),
    ("<slug:codelist_slug>/<str:tag_or_hash>/delete/", views.version_delete),
    (
        "<slug:codelist_slug>/<str:tag_or_hash>/diff/<other_tag_or_hash>/",
        views.version_diff,
    ),
    ("<slug:codelist_slug>/<str:tag_or_hash>/download.csv", views.version_download),
    (
        "<slug:codelist_slug>/<str:tag_or_hash>/definition.csv",
        views.version_download_definition,
    ),
    (
        "<slug:codelist_slug>/<str:tag_or_hash>/dmd-download.csv",
        views.version_dmd_download,
    ),
    ("<slug:codelist_slug>/<str:tag_or_hash>/dmd-convert", views.version_dmd_convert),
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
