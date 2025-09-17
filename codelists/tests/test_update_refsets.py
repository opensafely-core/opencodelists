import json
from pathlib import Path

from codelists.scripts.update_pcd_refsets import build_temp_config


def test_build_temp_config_updates_tag_and_release():
    db_release = "snomedct_test_20200101"
    latest_tag = "20200101"

    config_file = (
        Path(__file__).parent.parent / "scripts" / "nhsd_primary_care_refsets.json"
    )

    temp_path = build_temp_config(config_file, db_release, latest_tag)

    # Assert the temp file exists and contains the updated values
    assert Path(temp_path).exists()
    content = json.loads(Path(temp_path).read_text())
    assert content["organisation"] == "nhsd-primary-care-domain-refsets"
    assert content["tag"] == latest_tag
    assert content["coding_systems"]["snomedct"]["release"] == db_release
