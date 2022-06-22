from django.core.management import BaseCommand

from ...actions import update_draft_codeset
from ...models import CodelistVersion


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("version_hash")

    def handle(self, version_hash, **kwargs):
        draft = next(
            (
                version
                for version in CodelistVersion.objects.all()
                if version.hash == version_hash
            ),
            None,
        )
        if draft is None:
            self.stderr.write(f"No CodelistVersion found with hash '{version_hash}'")
        elif not draft.is_draft:
            self.stderr.write(
                f"CodelistVersion '{version_hash}' is not a draft ({draft.status})"
            )
        else:
            updates = update_draft_codeset(draft)
            if any(updates.values()):
                self.stdout.write(f"CodelistVersion {version_hash} updated:")
                if updates["added"]:
                    for code, status in updates["added"]:
                        self.stdout.write(f"{code} - {status} (new)")
                if updates["changed"]:
                    for code, status in updates["changed"]:
                        self.stdout.write(f"{code} - {status} (changed)")
                if updates["removed"]:
                    for code in updates["removed"]:
                        self.stdout.write(f"{code} (removed)")
            else:
                self.stdout.write(
                    f"CodelistVersion {version_hash}: no changes required"
                )
