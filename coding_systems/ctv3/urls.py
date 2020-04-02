from django.urls import path

from . import views

app_name = "ctv3"

urlpatterns = [
    path("", views.index, name="index"),
    path("concept/<read_code>/", views.concept, name="concept"),
    path("term/<term_id>/", views.term, name="term"),
]
