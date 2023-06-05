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
    Create a new draft from a CodelistVersion, using the most recent coding system release, ignoring
    any unknown code statuses if encountered. Then update the draft to fix any unknown codes that we
    can, and report the results.

    This command can be run to create and update a draft that cannot be generated in the builder
    UI in the usual way (i.e. `export_to_builder` raises an AssertionError because re-running the
    searched for a new draft imports new matching concepts).  At the moment,
    the builder frontend cannot deal with a CodeObj with status ?  if any of its ancestors are
    included or excluded. From the frontend, we just make the build fail so as not to magically
    add statuses for new concepts without users being made explicitly aware of them.
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
            ignore_unknown_statuses=True,
        )
        call_command("update_draft", draft.hash)
