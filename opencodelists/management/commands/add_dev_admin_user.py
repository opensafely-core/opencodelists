from datetime import datetime

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import BaseCommand
from django.db import transaction

from opencodelists.models import Membership, Organisation, User


class Command(BaseCommand):
    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise ValueError(
                "This command is for development use only and should not be run in production."
                "Ensure the DEBUG setting is set in development."
            )
        try:
            u = User.objects.get(username="BennettDeveloper")
        except ObjectDoesNotExist:
            u = User.objects.create_superuser(
                username="BennettDeveloper",
                email="bennettdeveloper@example.com",
                password="password123",
                name="Bennett Developer",
            )
        try:
            o = Organisation.objects.get(name="OpenSAFELY")
        except ObjectDoesNotExist:
            return
        Membership.objects.get_or_create(
            user=u,
            organisation=o,
            defaults={"is_admin": True, "date_joined": datetime.now()},
        )
