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
    CODING_SYSTEMS[coding_system_id] = mod.CodingSystem


def most_recent_database_alias(coding_system):
    return CODING_SYSTEMS[coding_system].get_by_release_or_most_recent().database_alias
