from django.urls import path

from . import views


app_name = "versioning"

urlpatterns = [
    path("latest-releases", views.latest_releases, name="latest_releases"),
    path("more-info/<str:coding_system>", views.more_info),
    path(
        "update-refset-version/<str:refset_type>",
        views.update_refset_version,
        name="update_refset_version",
    ),
]
