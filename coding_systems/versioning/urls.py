from django.urls import path

from . import views


app_name = "versioning"

urlpatterns = [path("latest-releases", views.latest_releases, name="latest_releases")]
