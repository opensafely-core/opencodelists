import csv
import os
from datetime import datetime
from pathlib import Path

from django.core.management import BaseCommand
from django.db import transaction
from django.db.models import F, Q

from codelists.models import Collaboration, Handle, SignOff
from opencodelists.models import Membership, User


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--no-dry-run",
            dest="dry_run",
            help="disable dry-run, actually delete users",
            default=True,
            action="store_false",
        )

    @transaction.atomic
    def handle(self, dry_run=True, **kwargs):
        # make a list of users we definitely don't want to remove

        # users with some association with a codelist
        users_with_codelists = (
            {
                h.user
                for h in Handle.objects.filter(user__isnull=False).prefetch_related(
                    "user"
                )
            }
            | {
                c.collaborator
                for c in Collaboration.objects.all().prefetch_related("collaborator")
            }
            | {s.user for s in SignOff.objects.all().prefetch_related("user")}
        )

        # TLDs we trust (.uk, .edu[.*], .ac.*, .gov[.*])
        safe_tld_users = User.objects.filter(
            Q(email__endswith=".uk")
            | Q(email__regex=r"[^@]+@.*(:?\.edu)(:?\.[^\.]+)?")
            | Q(email__regex=r"[^@]+@.*(:?\.ac)(:?\.[^\.]+)+")
            | Q(email__regex=r"[^@]+@.*(:?\.gov)(:?\.[^\.]+)?")
        )

        admins = User.objects.filter(is_admin=True)

        users_in_orgs = {m.user for m in Membership.objects.all()}

        removal_candidates = User.objects.exclude(
            username__in=[
                u.username
                for u in (
                    set(users_in_orgs)
                    | set(admins)
                    | users_with_codelists
                    | set(safe_tld_users)
                )
            ]
        )

        print(f"Users eligible for removal {len(removal_candidates)}")

        users_to_remove = User.objects.none()

        # heuristics for spammy users
        # too many dots
        three_dots_before_at = r"(?:[^\.]+\.){3,}[^\@]*\@.*"
        dotty = removal_candidates.filter(email__regex=three_dots_before_at)
        print(f"Three-or-more dots before @ users {len(dotty)}")
        users_to_remove |= dotty

        # bad TLDs
        for bad_tld in [
            ".dynainbox.com",
            ".fun",
            ".mo",
            ".online",
            ".pl",
            ".ru",
            ".shop",
            ".site",
            ".space",
            ".store",
            ".ua",
            "hotmails.com",
        ]:
            badtldusers = removal_candidates.filter(email__endswith=bad_tld)
            print(f"{bad_tld} email domain users {len(badtldusers)}")
            users_to_remove |= badtldusers

        # username equals name and no space in either
        badnames = removal_candidates.filter(username=F("name")).exclude(
            name__contains=" "
        )
        print(f"username equals name and no space in either {len(badnames)}")
        users_to_remove |= badnames

        print(f"Combined users to be removed {len(users_to_remove)}")
        userfields = [f.name for f in User._meta.fields]

        # dump them to csv just in case
        dump_path = Path(os.environ["DATABASE_DIR"]) / "deleted-user-dumps"
        dump_path.mkdir(parents=False, exist_ok=True)
        dump_file_path = dump_path / f"deletedusers_{datetime.now().isoformat()}.csv"
        with (dump_file_path).open("w") as f:
            writer = csv.DictWriter(f, fieldnames=userfields)
            writer.writeheader()
            writer.writerows(
                [{f: getattr(u, f) for f in userfields} for u in users_to_remove]
            )
            print(f"Spam user log written to {dump_file_path}")

        if not dry_run:
            for u in users_to_remove:
                u.delete()
            print(f"Deleted {len(users_to_remove)} users")
