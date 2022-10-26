from datetime import datetime, timezone

import pytest

from coding_systems.versioning.models import CodingSystemVersion


@pytest.fixture
def coding_system_version():
    yield CodingSystemVersion.objects.create(
        coding_system="snomedct",
        version="v1",
        import_ref="ref",
        valid_from=datetime(2022, 10, 1, tzinfo=timezone.utc),
    )
