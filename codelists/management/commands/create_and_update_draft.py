import structlog
from django.contrib.auth import get_user_model
from django.core.management import BaseCommand, call_command

from ...actions import export_to_builder
from ...coding_systems import most_recent_database_alias
from ...models import CodelistVersion


logger = structlog.get_logger()

User = get_user_model()


class Command(BaseCommand):

    """
    Create a new draft from a CodelistVersion, using the most recent coding system release. Then
    update the draft to assign statuses to any unknown codes that we can, and report the results.
    """

    def add_arguments(self, parser):
        parser.add_argument("version_hash")
        parser.add_argument("--author", help="author username")

    def handle(self, version_hash, author, **kwargs):
        if author is None:
            self.stderr.write("Author username is required")
            return

        try:
            author_obj = User.objects.get(username=author)
        except User.DoesNotExist:
            self.stderr.write(f"Author with username {author} not found")
            return

        codelist_version = next(
            (
                version
                for version in CodelistVersion.objects.all()
                if version.hash == version_hash
            ),
            None,
        )
        if codelist_version is None:
            self.stderr.write(f"No CodelistVersion found with hash '{version_hash}'")
            return

        draft = export_to_builder(
            version=codelist_version,
            author=author_obj,
            coding_system_database_alias=most_recent_database_alias(
                codelist_version.coding_system_id
            ),
        )
        call_command("update_draft", draft.hash)
        self.stdout.write(f"New draft created at {draft.get_absolute_url()}")
