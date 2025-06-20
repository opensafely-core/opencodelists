"""
Update a missing cached_hierarchy for all CodelistVersions in a given Coding System.

After making dm+d a BuilderCompatibleCodingSystem (i.e. supporting hierarchies),
various parts of the codebase make the assumption that all Codelists in a
BuilderCompatibileCodingSystem will have cached hierarchies.
This is not the case for Codelists created before the change to the CodingSystem.

This script should be run (and should only need to be run) after making such a change
to a CodingSystem.

./manage.py runscript update_missing_cached_hierarchies --script-args <coding_system_id>
"""

from traceback import print_exception

from codelists.actions import cache_hierarchy
from codelists.coding_systems import CODING_SYSTEMS
from codelists.models import CodelistVersion


def run(coding_system):
    if coding_system not in CODING_SYSTEMS:
        raise ValueError(
            f"Coding System {coding_system} not recognised.\nAvailable Coding Systems:\n{'\n'.join(CODING_SYSTEMS.keys())}"
        )

    versions_to_update = CodelistVersion.objects.filter(
        codelist__coding_system_id=coding_system
    ).filter(cached_hierarchy__isnull=True)

    print(f"{len(versions_to_update)} CodelistVersions to update")

    n = 0

    for codelist_version in versions_to_update:
        try:
            cache_hierarchy(version=codelist_version, hierarchy=None)
            n += 1
        except Exception as e:
            print(f"Error updating hierarchy for {codelist_version.get_absolute_url()}")
            print_exception(e)

    print(f"{n} CodelistVersions sucessfully updated")
