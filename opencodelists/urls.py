from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from . import views


users_patterns = [
    path("<username>/", views.user, name="user"),
    path(
        "<username>/new-codelist/",
        views.user_create_codelist,
        name="user-create-codelist",
    ),
]

organisations_patterns = [
    # list users for an organisation (admins only)
    path(
        "<organisation_slug>/users",
        views.organisation_members,
        name="organisation_members",
    ),
    path("", views.organisations, name="organisations"),
]

if settings.DEBUG_TOOLBAR:  # pragma: no cover
    debug_toolbar_urls = [path("__debug__/", include("debug_toolbar.urls"))]
else:
    debug_toolbar_urls = []

urlpatterns = [
    path("", include("codelists.urls")),
    path("api/v1/", include("codelists.api_urls")),
    path("users/", include(users_patterns)),
    path("superusers/", include("superusers.urls")),
    path("organisations/", include(organisations_patterns)),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/register/", views.register, name="register"),
    path("builder/", include("builder.urls")),
    path("conversions/", include("conversions.urls")),
    path("coding-systems/", include("coding_systems.versioning.urls")),
    path("docs/", include("userdocs.urls")),
    path("health-check/", views.health_check, name="health-check"),
    *debug_toolbar_urls,
    path("robots.txt", RedirectView.as_view(url=settings.STATIC_URL + "robots.txt")),
]
