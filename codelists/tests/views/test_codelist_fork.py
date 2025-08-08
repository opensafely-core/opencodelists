from ...models import Handle, Status
from .assertions import (
    assert_get_unauthenticated,
)
from .helpers import force_login


def test_get_unauthenticated(client, user_codelist):
    assert_get_unauthenticated(client, user_codelist.get_fork_url())


def test_get_success(client, user_codelist, collaborator):
    force_login(collaborator, client)
    response = client.get(user_codelist.get_fork_url())
    assert response.status_code == 302
    fork = Handle.objects.get(user=collaborator, slug=user_codelist.slug).codelist
    assert fork.versions.first().status == Status.UNDER_REVIEW
    assert response.url == fork.get_absolute_url()


def test_get_organisation_codelist(client, organisation_codelist, collaborator):
    force_login(collaborator, client)
    response = client.get(organisation_codelist.get_fork_url(), follow=True)
    # returns to the original codelist page, with a message that only user-owned
    # codelists can be forked
    assert (
        response.request["PATH_INFO"]
        == organisation_codelist.latest_visible_version(collaborator).get_absolute_url()
    )
    content = response.content.decode()
    assert "Only user-owned codelists can be forked" in content
