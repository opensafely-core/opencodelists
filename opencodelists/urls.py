from django.urls import include, path

urlpatterns = [
    path("", include("codelists.urls")),
    path("ctv3/", include("coding_systems.ctv3.urls")),
    path("snomedct/", include("coding_systems.snomedct.urls")),
]
