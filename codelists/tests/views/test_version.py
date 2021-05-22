def test_get_old_style_version(client, old_style_version):
    rsp = client.get(old_style_version.get_absolute_url())
    assert rsp.status_code == 200


def test_get_version_with_no_searches(client, version_with_no_searches):
    rsp = client.get(version_with_no_searches.get_absolute_url())
    assert rsp.status_code == 200


def test_get_version_with_some_searches(client, version_with_some_searches):
    rsp = client.get(version_with_some_searches.get_absolute_url())
    assert rsp.status_code == 200


def test_get_version_with_complete_searches(client, version_with_complete_searches):
    rsp = client.get(version_with_complete_searches.get_absolute_url())
    assert rsp.status_code == 200


def test_get_user_version(client, user_version):
    rsp = client.get(user_version.get_absolute_url())
    assert rsp.status_code == 200


def test_get_user_has_edit_permissions(client, user, version_with_no_searches):
    client.force_login(user)
    rsp = client.get(version_with_no_searches.get_absolute_url())
    assert rsp.status_code == 200
