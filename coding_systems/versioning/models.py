import dj_database_url
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS, connections, models
from django.db.migrations.executor import MigrationExecutor
from django.utils.text import slugify

from codelists.coding_systems import CODING_SYSTEMS


class ReleaseState(models.TextChoices):
    IMPORTING = "importing"  # the coding system release is being imported
    READY = "ready"  # the coding system release has been imported and is ready to use


class CodingSystemReleaseManager(models.Manager):
    def ready(self):
        return self.filter(state=ReleaseState.READY)

    def most_recent(self, coding_system):
        return (
            self.ready()
            .filter(coding_system=coding_system)
            .order_by("-valid_from")
            .first()
        )


class CodingSystemRelease(models.Model):
    coding_system = models.CharField(max_length=10)
    release_name = models.CharField(max_length=255)
    valid_from = models.DateField()
    import_timestamp = models.DateTimeField(auto_now_add=True)
    import_ref = models.TextField()
    database_alias = models.SlugField(max_length=255, unique=True)
    state = models.CharField(max_length=len("importing"), choices=ReleaseState.choices)

    objects = CodingSystemReleaseManager()

    class Meta:
        unique_together = ("coding_system", "release_name", "valid_from")

    def __str__(self):
        if self.release_name == "unknown":
            return self.release_name
        return f"{self.release_name} (valid from {self.valid_from.isoformat()})"

    def save(self, *args, **kwargs):
        # CodingSystem methods and the database router depend on the format
        # of database_alias following an expected pattern
        database_alias = slugify(
            f"{self.coding_system}_{self.release_name}_{self.valid_from.strftime('%Y%m%d')}"
        )
        if self.database_alias:
            assert self.database_alias == database_alias, (
                f"database_alias {self.database_alias} does not follow required pattern (expected '{database_alias}'"
            )
        else:
            self.database_alias = database_alias
        return super().save(*args, **kwargs)


def database_ready():
    connection = connections[DEFAULT_DB_ALIAS]
    connection.prepare_database()
    executor = MigrationExecutor(connection)
    targets = executor.loader.graph.leaf_nodes()
    versioning_plan = executor.migration_plan(targets)
    return not versioning_plan


def update_coding_system_database_connections(running_in_migration=False):
    """Add the database config for each coding system release"""
    # ensure that the database is ready and the CodingSystemRelease table is available
    # (i.e. migrations have been run)
    if running_in_migration or database_ready():  # pragma: no cover
        for coding_system_release in CodingSystemRelease.objects.all():
            if not CODING_SYSTEMS[coding_system_release.coding_system].has_database:
                continue
            db_path = build_db_path(coding_system_release)
            database_dict = {
                **connections.databases[DEFAULT_DB_ALIAS],
                **dj_database_url.parse(f"sqlite:///{db_path}"),
            }
            connections.databases[coding_system_release.database_alias] = database_dict


def build_db_path(coding_system_release):
    db_path = (
        settings.CODING_SYSTEMS_DATABASE_DIR
        / coding_system_release.coding_system
        / f"{coding_system_release.database_alias}.sqlite3"
    )

    return db_path


class NHSRefsetVersion(models.Model):
    release = models.CharField(max_length=255)
    tag = models.CharField(max_length=20)
    release_date = models.DateField()
    import_timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ["-release_date"]

    @classmethod
    def get_latest(cls):
        return cls.objects.first()


class PCDRefsetVersion(NHSRefsetVersion):
    """
    PCD Refset Version model. Clusters of codes used within various NHS business rules.
    (https://digital.nhs.uk/data-and-information/data-collections-and-data-sets/data-collections/quality-and-outcomes-framework-qof/quality-and-outcome-framework-qof-business-rules/primary-care-domain-reference-set-portal)
    """


class NHSDrugRefsetVersion(NHSRefsetVersion):
    """
    NHS Drug Refset Version model. Clusters of codes used within various NHS business rules.
    (https://digital.nhs.uk/data-and-information/data-collections-and-data-sets/data-collections/quality-and-outcomes-framework-qof/quality-and-outcome-framework-qof-business-rules/primary-care-domain-reference-set-portal)
    """
