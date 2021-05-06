from codelists.views.decorators import load_codelist, load_owner, load_version

request = object()


def test_load_owner_for_organisation(organisation):
    assert owner_view(request, organisation_slug=organisation.slug) == organisation


def test_load_owner_for_user(user):
    assert owner_view(request, username=user.username) == user


def test_load_organisation_codelist(organisation, organisation_codelist):
    assert (
        codelist_view(
            request,
            organisation_slug=organisation.slug,
            codelist_slug=organisation_codelist.slug,
        )
        == organisation_codelist
    )


def test_load_user_codelist(user, user_codelist):
    assert (
        codelist_view(
            request,
            username=user.username,
            codelist_slug=user_codelist.slug,
        )
        == user_codelist
    )


def test_load_version_by_hash(user, user_codelist, user_version):
    assert (
        version_view(
            request,
            username=user.username,
            codelist_slug=user_codelist.slug,
            tag_or_hash=user_version.hash,
        )
        == user_version
    )


def test_load_version_by_tag(user, user_codelist, user_version):
    user_version.tag = "20210127"  # This tag looks like a hash
    user_version.save()

    assert (
        version_view(
            request,
            username=user.username,
            codelist_slug=user_codelist.slug,
            tag_or_hash=user_version.tag,
        )
        == user_version
    )


def test_load_version_with_tag_by_hash(user, user_codelist, user_version):
    user_version.tag = "20210127"  # This tag looks like a hash
    user_version.save()

    assert (
        version_view(
            request,
            username=user.username,
            codelist_slug=user_codelist.slug,
            tag_or_hash=user_version.hash,
        )
        == user_version
    )


@load_owner
def owner_view(request, owner):
    return owner


@load_codelist
def codelist_view(request, codelist):
    return codelist


@load_version
def version_view(request, version):
    return version
