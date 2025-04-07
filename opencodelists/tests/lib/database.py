import os
from pathlib import Path

import dj_database_url
import pytest
from django.db import connections

import coding_systems
from opencodelists.settings import CODING_SYSTEMS_DATABASE_DIR


@pytest.mark.django_db(
    transaction=True,
    databases=[
        "default",
        "snomedct_test_20200101",
        "bnf_test_20200101",
        "icd10_test_20200101",
        "dmd_test_20200101",
        "ctv3_test_20200101",
    ],
)
def dump_all_test_data(universe):
    """
    This uses the `universe` of test fixtures of codelists, users, organisations etc.
    and their supporting core and coding system databases, and writes them to sqlite3
    files at paths which match the local configuration.

    This needs to access all of the test coding system databases so requires these all
    to be listed in pytest.mark.django_db's databases arg.
    `transaction=True` is also required (counterintuitively) such that the VACUUM command
    within backup() does not run within a transaction (which is not allowed).
    """
    for connection_name in connections.databases.keys():
        # we can't use settings.DATABASES here to get the usual on-disk paths for the
        # databases files as it's overwritten by the test initialisation

        # the coding system test databases' connection names are prefixed with the coding
        # system name.
        coding_system_name = connection_name.split("_")[0]
        if coding_system_name in dir(coding_systems):
            backup_path = (
                Path(CODING_SYSTEMS_DATABASE_DIR)
                / coding_system_name
                / f"{connection_name}.sqlite3"
            )
        else:  # "base"/"default" database
            # this URL fetch and parse is as per opencodelists/settings.py
            default_db_config = dj_database_url.parse(
                os.environ.get("DATABASE_URL", default="sqlite:///db.sqlite3")
            )
            backup_path = Path(default_db_config["NAME"])
        backup_path.unlink(missing_ok=True)
        backup(backup_path, connection=connections[connection_name])


def backup(backup_path, connection=connections["default"]):
    cur = connection.cursor()
    cur.execute(f"VACUUM main INTO '{backup_path}';")
