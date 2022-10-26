from django.apps import AppConfig


class VersioningConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "coding_systems.versioning"

    def ready(self):
        from .models import update_coding_system_database_connections

        update_coding_system_database_connections()
