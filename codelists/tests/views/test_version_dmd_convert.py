from ...actions import convert_bnf_codelist_version_to_dmd
from ...models import Handle, Status
from .assertions import assert_post_unauthenticated, assert_post_unauthorised
from .helpers import force_login


def test_post_unauthenticated(client, bnf_version_asthma):
    assert_post_unauthenticated(client, bnf_version_asthma.get_dmd_convert_url())


def test_post_unauthorised(client, bnf_version_asthma):
    assert_post_unauthorised(client, bnf_version_asthma.get_dmd_convert_url())


def test_post_success(client, bnf_version_asthma):
    force_login(bnf_version_asthma, client)
    response = client.post(bnf_version_asthma.get_dmd_convert_url())
    assert response.status_code == 302
    converted_dmd_codelist = Handle.objects.get(
        slug=f"{bnf_version_asthma.codelist.slug}-dmd"
    ).codelist
    assert converted_dmd_codelist.versions.first().status == Status.UNDER_REVIEW

    assert response.url == converted_dmd_codelist.get_absolute_url()


def test_post_already_exists(client, bnf_version_asthma):
    dmd_codelist = convert_bnf_codelist_version_to_dmd(bnf_version_asthma)
    force_login(bnf_version_asthma, client)
    response = client.post(bnf_version_asthma.get_dmd_convert_url(), follow=True)
    # returns to the bnf version page, with a message that the converted codelist
    # already exists, and a link to it
    assert response.request["PATH_INFO"] == bnf_version_asthma.get_absolute_url()
    content = response.content.decode()
    assert "already exists" in content
    assert dmd_codelist.get_absolute_url() in content
