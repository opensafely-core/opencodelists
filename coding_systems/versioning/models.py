import dj_database_url
from django.conf import settings
from django.db import connections, models

from opencodelists.hash_utils import hash, unhash


class CodingSystemVersionManager(models.Manager):
    def get_by_hash(self, hash):
        """Return the CodingSystemVersion with given hash."""
        id = unhash(hash, "CodingSystemVersion")
        return self.get(id=id)


class CodingSystemVersion(models.Model):
    coding_system = models.CharField(max_length=10)
    version = models.CharField(max_length=255, null=True, blank=True)
    valid_from = models.DateField()
    import_timestamp = models.DateTimeField(auto_now_add=True)
    import_ref = models.TextField()

    objects = CodingSystemVersionManager()

    class Meta:
        unique_together = ("coding_system", "valid_from")

    @classmethod
    def latest(cls, coding_system):
        return (
            cls.objects.filter(coding_system=coding_system)
            .order_by("-valid_from")
            .first()
        )

    @property
    def hash(self):
        return hash(self.id, "CodingSystemVersion")

    @property
    def db_name(self):
        return f"{self.coding_system}_{self.hash}"


def get_coding_system_database_connections():
    """Add the database config for each coding system version"""
    for coding_system_version in CodingSystemVersion.objects.all():
        db_path = settings.DATABASE_DIR / f"{coding_system_version.db_name}.sqlite3"
        database_dict = {
            **connections.databases["default"],
            **dj_database_url.parse(f"sqlite:///{db_path}"),
        }
        connections.databases[coding_system_version.db_name] = database_dict


get_coding_system_database_connections()
