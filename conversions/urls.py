from django.urls import path

from . import views

app_name = "conversions"

urlpatterns = [
    path("", views.convert, name="convert"),
]
