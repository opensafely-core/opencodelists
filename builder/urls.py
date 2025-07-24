from django.urls import path

from . import views


app_name = "builder"


urlpatterns = [
    path("<hash>/", views.draft, name="draft"),
    path("<hash>/api/references", views.references),
    # Note that search_slug isn't actually guaranteed to match Django's concept
    # of a slug, so we use the str: path converter instead of slug:
    # See builder/actions.py::create_search_slug
    path(
        "<hash>/search/<int:search_id>/<str:search_slug>/", views.search, name="search"
    ),
    path(
        "<hash>/search/<int:search_id>/<str:search_slug>/delete/",
        views.delete_search,
        name="delete-search",
    ),
    path("<hash>/no-search-term/", views.no_search_term, name="no-search-term"),
    path("<hash>/update/", views.update, name="update"),
    path("<hash>/search/", views.new_search, name="new-search"),
]
