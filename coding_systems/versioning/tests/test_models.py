from datetime import datetime, timezone

import pytest
from django.db import connections
from django.db.utils import OperationalError
from django.utils.connection import ConnectionDoesNotExist

from coding_systems.snomedct.models import Concept
from coding_systems.versioning.models import (
    CodingSystemRelease,
    ReleaseState,
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
        state=ReleaseState.READY,
    )
    # most_recent is coding system-dependent, so a later valid_from version
    # for a different coding system is irrelevant
    CodingSystemRelease.objects.create(
        coding_system="dmd",
        release_name="v1",
        import_ref="ref",
        valid_from=datetime(2022, 10, 15, tzinfo=timezone.utc),
        state=ReleaseState.READY,
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
        state=ReleaseState.READY,
    )
    update_coding_system_database_connections()
    assert null_coding_system_release.database_alias not in connections.databases


@pytest.mark.parametrize(
    "alias,slugified_alias",
    [(None, "null_version-1_20221001"), ("", "null_version-1_20221001")],
)
def test_coding_system_default_database_alias(alias, slugified_alias):
    # database_alias is set on save, to a slug in the format
    # <coding_system>_<release_name>_<valid_from>
    csr = CodingSystemRelease.objects.create(
        coding_system="null",
        release_name="Version 1",
        valid_from=datetime(2022, 10, 1, tzinfo=timezone.utc),
        database_alias=alias,
        state=ReleaseState.READY,
    )
    assert csr.database_alias == slugified_alias


def test_coding_system_invalid_database_alias():
    # If a custom database_alias is set, and doesn't match the required database_alias
    # pattern, an AssertionError is raised
    with pytest.raises(AssertionError):
        CodingSystemRelease.objects.create(
            coding_system="null",
            release_name="Version 1",
            valid_from=datetime(2022, 10, 1, tzinfo=timezone.utc),
            database_alias="custom_db_alias",
            state=ReleaseState.READY,
        )

    # make a CSR with the default alias
    csr = CodingSystemRelease.objects.create(
        coding_system="null",
        release_name="Version 1",
        valid_from=datetime(2022, 10, 1, tzinfo=timezone.utc),
        state=ReleaseState.READY,
    )
    # if any of the component fields are changed, the db alias must be updated too
    with pytest.raises(AssertionError):
        csr.release_name = "Version 2"
        csr.save()

    csr.release_name = "Version 2"
    csr.database_alias = "null_version-2_20221001"
    csr.save()


def test_updating_database_alias_with_update_or_create():
    # As of Django 4.2, update_or_create passes update_fields
    # to Model.save()
    # This means that any fields that are updated in a custom
    # save() method need to be added to update_fields in order to
    # ensure that they are also saved
    # https://docs.djangoproject.com/en/4.2/releases/4.2/#setting-update-fields-in-model-save-may-now-be-required
    #
    # The custom CodingSystemRelease.save() method updates database_alias
    # based on release_name, coding_system and valid_from fields.
    # This test ensures that, although we aren't adding database_alias to
    # update_fields, the validation in the save method will raise an error
    # in update_or_create if database_alias is not also updated.
    csr = CodingSystemRelease.objects.create(
        coding_system="null",
        release_name="Version 1",
        valid_from=datetime(2022, 10, 1, tzinfo=timezone.utc),
        state=ReleaseState.READY,
    )
    queryset = CodingSystemRelease.objects.filter(id=csr.id)
    with pytest.raises(AssertionError):
        queryset.update_or_create(id=csr.id, defaults={"release_name": "Version 2"})

    queryset.update_or_create(
        id=csr.id, defaults={"release_name": "Version 2", "database_alias": None}
    )
    csr.refresh_from_db()
    assert csr.database_alias == "null_version-2_20221001"


def test_coding_system_release_state(coding_system_release):
    initial_count = CodingSystemRelease.objects.count()
    # create a new CSR, with importing state
    now = datetime.now()
    importing_cs = CodingSystemRelease.objects.create(
        coding_system="snomedct",
        release_name="vtest",
        valid_from=now,
        state=ReleaseState.IMPORTING,
    )

    # The importing CSR doesn't get included in `ready`
    assert CodingSystemRelease.objects.ready().count() == initial_count
    assert CodingSystemRelease.objects.count() == initial_count + 1
    assert CodingSystemRelease.objects.most_recent("snomedct") != importing_cs

    importing_cs.state = ReleaseState.READY
    importing_cs.save()
    assert CodingSystemRelease.objects.ready().count() == initial_count + 1
    assert CodingSystemRelease.objects.most_recent("snomedct") == importing_cs
