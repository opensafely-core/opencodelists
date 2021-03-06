import debug_toolbar
from django.contrib import admin
from django.urls import include, path

from . import views

users_patterns = [
    path("activate/<token>/", views.user_set_password, name="user-set-password"),
    path("added/<username>/", views.user_activation_url, name="user-activation-url"),
    path("<username>/", views.user, name="user"),
    path(
        "<username>/new-codelist/",
        views.user_create_codelist,
        name="user-create-codelist",
    ),
]

urlpatterns = [
    path("", include("codelists.urls")),
    path("api/v1/", include("codelists.api_urls")),
    path("users/", include(users_patterns)),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/register/", views.register, name="register"),
    path("builder/", include("builder.urls")),
    path("conversions/", include("conversions.urls")),
    path("docs/", include("docs.urls")),
    path("ctv3/", include("coding_systems.ctv3.urls")),
    path("snomedct/", include("coding_systems.snomedct.urls")),
    path("__debug__/", include(debug_toolbar.urls)),
]
