import dj_database_url
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS, connections, models
from django.db.migrations.executor import MigrationExecutor
from django.utils.text import slugify

from codelists.coding_systems import CODING_SYSTEMS


class CodingSystemReleaseManager(models.Manager):
    def most_recent(self, coding_system):
        return self.filter(coding_system=coding_system).order_by("-valid_from").first()


class CodingSystemRelease(models.Model):
    coding_system = models.CharField(max_length=10)
    release_name = models.CharField(max_length=255)
    valid_from = models.DateField()
    import_timestamp = models.DateTimeField(auto_now_add=True)
    import_ref = models.TextField()
    database_alias = models.SlugField(max_length=255, unique=True)

    objects = CodingSystemReleaseManager()

    class Meta:
        unique_together = ("coding_system", "release_name", "valid_from")

    def save(self, *args, **kwargs):
        if not self.database_alias:
            self.database_alias = slugify(
                f"{self.coding_system}_{self.release_name}_{self.valid_from.strftime('%Y%m%d')}"
            )
        return super().save(*args, **kwargs)


def database_ready():
    connection = connections[DEFAULT_DB_ALIAS]
    connection.prepare_database()
    executor = MigrationExecutor(connection)
    targets = executor.loader.graph.leaf_nodes()
    versioning_plan = executor.migration_plan(targets)
    return not versioning_plan


def update_coding_system_database_connections():
    """Add the database config for each coding system release"""
    # ensure that the database is ready and the CodingSystemRelease table is available
    # (i.e. migrations have been run)
    if database_ready():  # pragma: no cover
        for coding_system_release in CodingSystemRelease.objects.all():
            if not CODING_SYSTEMS[coding_system_release.coding_system].has_database:
                continue
            db_path = (
                settings.CODING_SYSTEMS_DATABASE_DIR
                / coding_system_release.coding_system
                / f"{coding_system_release.database_alias}.sqlite3"
            )
            database_dict = {
                **connections.databases[DEFAULT_DB_ALIAS],
                **dj_database_url.parse(f"sqlite:///{db_path}"),
            }
            connections.databases[coding_system_release.database_alias] = database_dict
