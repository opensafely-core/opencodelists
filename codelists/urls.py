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
    path("codelist/<organisation_slug>/", views.index, name="organisation_index"),
]

for subpath, view in [
    ("add/", views.codelist_create),
    ("<codelist_slug>/", views.codelist),
    ("<codelist_slug>/edit/", views.codelist_update),
    ("<codelist_slug>/upload-version/", views.version_upload),
    ("<codelist_slug>/<tag_or_hash>/", views.version),
    ("<codelist_slug>/<tag_or_hash>/create-new-version/", views.version_create),
    ("<codelist_slug>/<tag_or_hash>/publish/", views.version_publish),
    ("<codelist_slug>/<tag_or_hash>/download.csv", views.version_download),
    ("<codelist_slug>/<tag_or_hash>/dmd-download.csv", views.version_dmd_download),
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
