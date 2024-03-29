def test_get_user_has_edit_permissions(client, user, codelist, latest_version):
    client.force_login(user)
    rsp = client.get(codelist.get_absolute_url(), follow=True)
    assert rsp.status_code == 200
    assert rsp.redirect_chain[-1][0] == latest_version.get_absolute_url()


def test_get_user_doesnt_have_edit_permissions(
    client, codelist, latest_published_version
):
    rsp = client.get(codelist.get_absolute_url(), follow=True)
    assert rsp.status_code == 200
    assert rsp.redirect_chain[-1][0] == latest_published_version.get_absolute_url()


def test_get_no_versions_available(client, codelist_from_scratch):
    rsp = client.get(codelist_from_scratch.get_absolute_url(), follow=True)
    assert rsp.status_code == 200
    assert rsp.redirect_chain[-1][0] == "/"
