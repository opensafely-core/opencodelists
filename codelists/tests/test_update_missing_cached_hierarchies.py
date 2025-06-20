import pytest

from codelists.coding_systems import CODING_SYSTEMS

from ..scripts.update_missing_cached_hierarchies import run


def test_update_missing_cached_hierarchies_unknown_coding_system():
    coding_system = "test"
    with pytest.raises(
        ValueError, match=f"Coding System {coding_system} not recognised"
    ) as e:
        run(coding_system)
        for cs in CODING_SYSTEMS.keys():
            assert cs in str(e)


def test_update_missing_cached_hierarchies_none_to_update(dmd_codelist, capsys):
    run("dmd")

    assert "0 CodelistVersions to update" in capsys.readouterr().out


def test_update_missing_cached_hierarchies_one_to_update(dmd_codelist, capsys):
    version = dmd_codelist.versions.first()
    version.cached_hierarchy.delete()
    version.save()

    run("dmd")

    assert "1 CodelistVersions to update" in capsys.readouterr().out
    assert hasattr(version, "cached_hierarchy")
