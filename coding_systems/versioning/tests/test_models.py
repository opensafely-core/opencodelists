from datetime import datetime, timezone

import pytest
from django.db import connections
from django.db.utils import OperationalError
from django.utils.connection import ConnectionDoesNotExist

from coding_systems.snomedct.models import Concept
from coding_systems.versioning.models import (
    CodingSystemVersion,
    update_coding_system_database_connections,
)


def test_coding_system_version_db_name(coding_system_version):
    assert coding_system_version.db_name == "snomedct_v1_20221001"


def test_coding_system_version_most_recent(coding_system_version):
    # most_recent depends on valid_from date, not imported date
    # make a later import, but for an earlier version
    new_cs_version = CodingSystemVersion.objects.create(
        coding_system="snomedct",
        version="v0.1",
        import_ref="ref",
        valid_from=datetime(2022, 9, 1, tzinfo=timezone.utc),
    )
    # most_recent is coding system-dependent, so a later valid_from version
    # for a different coding system is irrelevant
    CodingSystemVersion.objects.create(
        coding_system="dmd",
        version="v1",
        import_ref="ref",
        valid_from=datetime(2022, 10, 15, tzinfo=timezone.utc),
    )

    assert new_cs_version.import_timestamp > coding_system_version.import_timestamp
    assert CodingSystemVersion.objects.most_recent("snomedct") == coding_system_version

    # an unknown coding system
    assert CodingSystemVersion.objects.most_recent("foo") is None


def test_update_coding_system_database_connections(coding_system_version):
    # The coding_system_version fixture is created after django setup, so the database
    # connection isn't there yet
    assert coding_system_version.db_name not in connections.databases
    with pytest.raises(ConnectionDoesNotExist):
        Concept.objects.using(coding_system_version.db_name).exists()

    update_coding_system_database_connections()
    assert coding_system_version.db_name in connections.databases
    # Now the connection is available, but the database doesn't exist yet
    with pytest.raises(OperationalError, match="no such table: snomedct_concept"):
        Concept.objects.using(coding_system_version.db_name).exists()
