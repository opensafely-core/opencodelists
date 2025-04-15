from django.urls import path

from . import views


app_name = "builder"

urlpatterns = [
    path("<hash>/", views.draft, name="draft"),
    path("<hash>/search/<search_id>/<search_slug>/", views.search, name="search"),
    path(
        "<hash>/search/<search_id>/<search_slug>/delete/",
        views.delete_search,
        name="delete-search",
    ),
    path("<hash>/no-search-term/", views.no_search_term, name="no-search-term"),
    path("<hash>/update/", views.update, name="update"),
    path("<hash>/search/", views.new_search, name="new-search"),
]
