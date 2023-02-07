from django.urls import path

from . import views

app_name = "versioning"

urlpatterns = [
    # There was a typo in the codelist names.  If this happens a lot, we could
    # add a "formerly known as" field to Codelist.
    path("latest-releases", views.latest_releases, name="latest_releases")
]
