from opencodelists.models import User


def test_get(client, organisation_user):
    user = User.objects.create(
        username="test", name="test", email="test@test.com", password="test"
    )
    client.force_login(user)
    response = client.get("/users/test/")
    assert response.status_code == 200
    assert not response.context["codelists"]
    assert not response.context["under_review"]
    assert not response.context["drafts"]


def test_get_with_codelists(client, draft, version_under_review, user_codelist):
    user = User.objects.create(
        username="test", name="test", email="test@test.com", password="test"
    )

    for codelist in [draft, version_under_review]:
        codelist.draft_owner = user
        codelist.save()

    handle = user_codelist.handles.first()
    handle.user = user
    handle.save()

    client.force_login(user)
    response = client.get("/users/test/")
    assert response.status_code == 200

    assert [cl.id for cl in response.context["codelists"]] == [user_codelist.id]
    assert [cl.id for cl in response.context["under_review"]] == [
        version_under_review.id
    ]
    assert [cl.id for cl in response.context["drafts"]] == [draft.id]
