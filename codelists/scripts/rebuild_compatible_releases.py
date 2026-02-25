from django.db.utils import OperationalError

from codelists.coding_systems import CODING_SYSTEMS
from coding_systems.base.import_data_utils import (
    update_codelist_version_compatibility,
    update_coding_system_database_connections,
)
from coding_systems.versioning.models import CodingSystemRelease


def run():
    update_coding_system_database_connections()
    for coding_system in CODING_SYSTEMS:
        # We will be computing the compatiblity of CodelistVersions that are compatible with the prior
        # release of a coding system against the following release so release order is important here
        for i, release in enumerate(
            CodingSystemRelease.objects.filter(coding_system=coding_system).order_by(
                "valid_from"
            )
        ):
            # The first release has no "prior" release so exclude
            if i == 0:
                continue
            while True:
                failcount = 0
                try:
                    update_codelist_version_compatibility(
                        coding_system, release.database_alias
                    )
                except OperationalError as e:
                    if failcount == 5:
                        raise RuntimeError(
                            "More than 5 database is locked errors encountered"
                        )
                    elif "database is locked" in str(e):
                        failcount += 1
                        continue
                    else:
                        raise e
                break
