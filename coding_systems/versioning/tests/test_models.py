from datetime import datetime, timezone

import pytest
from django.db import connections
from django.db.utils import OperationalError
from django.utils.connection import ConnectionDoesNotExist

from coding_systems.snomedct.models import Concept
from coding_systems.versioning.models import (
    CodingSystemRelease,
    update_coding_system_database_connections,
)


def test_coding_system_release_most_recent(coding_system_release):
    # most_recent depends on valid_from date, not imported date
    # make a later import, but for an earlier version
    new_cs_release = CodingSystemRelease.objects.create(
        coding_system="snomedct",
        release_name="v0.1",
        import_ref="ref",
        valid_from=datetime(2022, 9, 1, tzinfo=timezone.utc),
    )
    # most_recent is coding system-dependent, so a later valid_from version
    # for a different coding system is irrelevant
    CodingSystemRelease.objects.create(
        coding_system="dmd",
        release_name="v1",
        import_ref="ref",
        valid_from=datetime(2022, 10, 15, tzinfo=timezone.utc),
    )

    assert new_cs_release.import_timestamp > coding_system_release.import_timestamp
    assert CodingSystemRelease.objects.most_recent("snomedct") == coding_system_release

    # an unknown coding system
    assert CodingSystemRelease.objects.most_recent("foo") is None


def test_update_coding_system_database_connections(
    coding_systems_tmp_path, coding_system_release
):
    # The coding_system_release fixture is created after django setup, so the database
    # connection isn't there yet
    assert coding_system_release.database_alias not in connections.databases
    with pytest.raises(ConnectionDoesNotExist):
        Concept.objects.using(coding_system_release.database_alias).exists()

    update_coding_system_database_connections()
    assert coding_system_release.database_alias in connections.databases
    # Now the connection is available, but the database doesn't exist yet
    with pytest.raises(OperationalError, match="no such table: snomedct_concept"):
        Concept.objects.using(coding_system_release.database_alias).exists()


def test_update_dummy_coding_system_database_connections(coding_systems_tmp_path):
    # A CodingSystemRelease is created for null/opcs4 coding systems, but
    # is not associated with a database, so they don't get added to the database
    # connections
    null_coding_system_release = CodingSystemRelease.objects.create(
        coding_system="null",
        release_name="null",
        import_ref="ref",
        valid_from=datetime(2022, 10, 1, tzinfo=timezone.utc),
    )
    update_coding_system_database_connections()
    assert null_coding_system_release.database_alias not in connections.databases
