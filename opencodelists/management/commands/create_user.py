from datetime import datetime

from django.core.management import BaseCommand
from django.db import transaction

from opencodelists.models import Membership, Organisation, User


class Command(BaseCommand):
    """Create or update a User."""

    help = "Create or update a User"

    def add_arguments(self, parser):
        parser.add_argument("username", help="User to create or update")
        parser.add_argument("--email", help="Defaults to username@example.com")
        parser.add_argument("--name", help="Defaults to username")
        parser.add_argument("-p", "--password", help="Required if creating new user")
        parser.add_argument(
            "-o", "--organisation", help="Name of organisation to add user to, optional"
        )
        parser.add_argument(
            "--admin",
            action="store_true",
            help="Make user admin/superuser",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        username = options["username"]

        # We cannot use get_or_create here because the create_user factory function
        # is special, and does additional things when creating users.
        created = False
        try:
            user = User.objects.get(username=username)

            updated = False
            if options["admin"]:
                user.is_admin = True
                updated = True
            if options["password"]:
                user.set_password(options["password"])
                updated = True
            if options["email"]:
                user.email = options["email"]
                updated = True
            if options["name"]:
                user.name = options["name"]
                updated = True
            if updated:
                user.save()
        except User.DoesNotExist:
            if not options["password"]:
                raise ValueError("Password must be supplied for new user creation")

            user = User.objects.create_user(
                username=username,
                password=options["password"],
                email=options["email"] or f"{username}@example.com",
                name=options["name"] or username,
                is_admin=options["admin"],
            )
            created = True

        if options["organisation"]:
            organisation = Organisation.objects.get(name=options["organisation"])
            Membership.objects.get_or_create(
                user=user,
                organisation=organisation,
                defaults={"is_admin": True, "date_joined": datetime.now()},
            )
            updated = True

        self.stdout.write(
            f"User {username} {'created' if created else 'updated' if updated else 'unchanged'}"
        )
