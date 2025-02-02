import pytest
from django.core.management import call_command

from opencodelists.models import Membership, User


def test_create_user_defaults(capsys):
    call_command("create_user", "username", "--password=foobar123")

    user = User.objects.get(username="username")
    assert user.email == "username@example.com"
    assert user.name == "username"
    assert user.check_password("foobar123")
    assert not user.is_admin

    captured = capsys.readouterr()
    assert "User username created" in captured.out

    # test idempotency
    call_command("create_user", "username", "--password=foobar123")

    user = User.objects.get(username="username")
    assert user.email == "username@example.com"
    assert user.name == "username"
    assert user.check_password("foobar123")
    assert not user.is_admin


def test_create_user_args(capsys, organisation):
    call_command(
        "create_user",
        "username",
        "--email=foo@bar.com",
        "--name=fullname",
        "--admin",
        "--password=foobar123",
        f"--o={organisation.name}",
    )

    user = User.objects.get(username="username")
    assert user.email == "foo@bar.com"
    assert user.name == "fullname"
    assert user.is_admin
    assert user.check_password("foobar123")
    assert Membership.objects.filter(user=user, organisation=organisation).exists()

    captured = capsys.readouterr()
    assert "User username created" in captured.out

    # test idempotency
    call_command(
        "create_user",
        "username",
        "--email=foo@bar.com",
        "--name=fullname",
        "--admin",
        "--password=foobar123",
        f"--o={organisation.name}",
    )

    user = User.objects.get(username="username")
    assert user.email == "foo@bar.com"
    assert user.name == "fullname"
    assert user.is_admin
    assert user.check_password("foobar123")
    assert Membership.objects.filter(user=user, organisation=organisation).exists()


def test_create_user_without_password_fails():
    with pytest.raises(ValueError):
        call_command("create_user", "username")


def test_update_user(capsys, user_without_organisation, organisation):
    username = user_without_organisation.username

    call_command(
        "create_user",
        username,
        "--email=foo@bar.com",
        "--name=fullname",
        "--admin",
        "--password=foobar123",
        f"--o={organisation.name}",
    )

    user = User.objects.get(username=username)
    assert user.email == "foo@bar.com"
    assert user.name == "fullname"
    assert user.is_admin
    assert user.check_password("foobar123")
    assert Membership.objects.filter(user=user, organisation=organisation).exists()

    captured = capsys.readouterr()
    assert f"User {username} updated" in captured.out

    # test idempotency
    call_command(
        "create_user",
        username,
        "--email=foo@bar.com",
        "--name=fullname",
        "--admin",
        "--password=foobar123",
        f"--o={organisation.name}",
    )

    user = User.objects.get(username=username)
    assert user.email == "foo@bar.com"
    assert user.name == "fullname"
    assert user.is_admin
    assert user.check_password("foobar123")
    assert Membership.objects.filter(user=user, organisation=organisation).exists()
