import glob
import os
from importlib import import_module

from django.conf import settings


CODING_SYSTEMS = {}

for path in glob.glob(
    os.path.join(settings.BASE_DIR, "coding_systems", "*", "coding_system.py")
):
    coding_system_id = path.split(os.path.sep)[-2]
    mod = import_module(f"coding_systems.{coding_system_id}.coding_system")
    coding_system = mod.CodingSystem
    CODING_SYSTEMS[coding_system.id] = coding_system


def most_recent_database_alias(coding_system_id):
    return (
        CODING_SYSTEMS[coding_system_id].get_by_release_or_most_recent().database_alias
    )


def builder_compatible_coding_systems():
    return sorted(
        [
            system
            for system in CODING_SYSTEMS.values()
            if system.is_builder_compatible()
        ],
        key=lambda x: x.name.lower(),
    )
