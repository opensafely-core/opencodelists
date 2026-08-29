from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from . import views
from .views.errors import bad_request, page_not_found, permission_denied, server_error


handler400 = bad_request
handler403 = permission_denied
handler404 = page_not_found
handler500 = server_error

users_patterns = [
    path("<slug:username>/", views.user, name="user"),
    path(
        "<slug:username>/new-codelist/",
        views.user_create_codelist,
        name="user-create-codelist",
    ),
    path(
        "<slug:username>/csv-descendants-preview/",
        views.csv_descendants_preview,
        name="csv-descendants-preview",
    ),
]

organisations_patterns = [
    # list users for an organisation (admins only)
    path(
        "<slug:organisation_slug>/users",
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
    path("contact/", views.contact, name="contact"),
    path("400", bad_request, name="bad_request"),
    path("403", permission_denied, name="permission_denied"),
    path("404", page_not_found, name="page_not_found"),
    path("500", server_error, name="server_error"),
    path("health-check/", views.health_check, name="health-check"),
    *debug_toolbar_urls,
    path("robots.txt", RedirectView.as_view(url=settings.STATIC_URL + "robots.txt")),
]
