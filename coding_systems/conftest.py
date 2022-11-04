from datetime import datetime, timezone

import pytest

from codelists.coding_systems import CODING_SYSTEMS
from coding_systems.versioning.models import CodingSystemRelease


@pytest.fixture
def coding_system_release():
    yield CodingSystemRelease.objects.create(
        coding_system="snomedct",
        version="v1",
        import_ref="ref",
        valid_from=datetime(2022, 10, 1, tzinfo=timezone.utc),
    )


@pytest.fixture
def coding_systems_tmp_path(settings, tmp_path):
    settings.CODING_SYSTEMS_DATABASE_DIR = tmp_path
    for coding_system in CODING_SYSTEMS:
        (tmp_path / coding_system).mkdir(parents=True, exist_ok=True)
    yield tmp_path
