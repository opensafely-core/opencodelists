from django.urls import path

from . import views

app_name = "builder"

urlpatterns = [
    path("", views.index, name="index"),
    path("<username>/", views.user, name="user"),
    path("<username>/<codelist_slug>/", views.codelist, name="codelist"),
    path(
        "<username>/<codelist_slug>/search/<search_slug>/",
        views.codelist,
        name="search",
    ),
    path(
        "<username>/<codelist_slug>/no-search-term/",
        views.codelist,
        {"search_slug": views.NO_SEARCH_TERM},
        name="no-search-term",
    ),
    path("<username>/<codelist_slug>/update/", views.update, name="update"),
    path("<username>/<codelist_slug>/search/", views.new_search, name="new_search"),
    path("<username>/<codelist_slug>/download.csv", views.download, name="download"),
    path(
        "<username>/<codelist_slug>/download-dmd.csv",
        views.download_dmd,
        name="download-dmd",
    ),
]
