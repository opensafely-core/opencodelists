from ...models import Handle, Status
from .assertions import (
    assert_get_unauthenticated,
)
from .helpers import force_login


def test_get_unauthenticated(client, user_codelist):
    assert_get_unauthenticated(client, user_codelist.get_clone_url())


def test_get_success(client, user_codelist, collaborator):
    force_login(collaborator, client)
    response = client.get(user_codelist.get_clone_url())
    assert response.status_code == 302
    clone = Handle.objects.get(user=collaborator, slug=user_codelist.slug).codelist
    assert clone.versions.first().status == Status.UNDER_REVIEW
    assert response.url == clone.get_absolute_url()
