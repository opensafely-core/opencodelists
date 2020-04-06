from django.urls import path

from . import views

app_name = "snomedct"

urlpatterns = [
    path("concept/<id>/", views.concept, name="concept"),
]
