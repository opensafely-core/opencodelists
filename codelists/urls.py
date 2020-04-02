from django.urls import path

from . import views

app_name = "codelists"

urlpatterns = [
    path("", views.index, name="index"),
    path("codelist/<publisher_slug>/<codelist_slug>/", views.codelist, name="codelist"),
]
