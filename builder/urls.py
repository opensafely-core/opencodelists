from django.urls import path

from . import views

app_name = "builder"

urlpatterns = [
    path("", views.index, name="index"),
    path("<username>/", views.user, name="user"),
    path("<username>/<codelist_slug>/", views.codelist, name="codelist"),
    path(
        "<username>/<codelist_slug>/search/<search_slug>/", views.search, name="search",
    ),
    path("<username>/<codelist_slug>/results/", views.results, name="results"),
]
