from django.urls import path

from . import views

app_name = "snomedct"

urlpatterns = [
    path("concept/<id>/", views.concept, name="concept"),
    path("concept/<id>/paths/", views.concept_paths, name="concept-paths"),
]
