import debug_toolbar
from django.contrib import admin
from django.urls import include, path

from . import views

users_patterns = [
    path("add/", views.UserCreate.as_view(), name="user-create"),
]

urlpatterns = [
    path("", include("codelists.urls")),
    path("users/", include(users_patterns)),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("builder/", include("builder.urls")),
    path("ctv3/", include("coding_systems.ctv3.urls")),
    path("snomedct/", include("coding_systems.snomedct.urls")),
    path("project/<project_slug>/", views.project, name="project"),
    path("__debug__/", include(debug_toolbar.urls)),
]
