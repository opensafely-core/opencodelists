from datetime import date
from pathlib import Path
from unittest.mock import patch

from coding_systems.conftest import mock_migrate_coding_system
from coding_systems.snomedct.import_data import import_data
from coding_systems.snomedct.models import Concept
from coding_systems.versioning.models import CodingSystemRelease

MOCK_SNOMEDCT_IMPORT_DATA_PATH = (
    Path(__file__).parents[1] / "fixtures" / "import_resources" / "snomed.zip"
)


def test_import_data(coding_systems_tmp_path, settings):

    cs_release_count = CodingSystemRelease.objects.count()

    # import mock data
    # This consists of a very small subset of 6 Snomed concepts
    #
    # 3723001        Arthritis
    # 439656005        └ Arthritis of elbow
    # 202855006           └ Lateral epicondylitis
    # 312411000119100        ├ Lateral epicondylitis of left humerus
    # 15636001000119108      |  └ Lateral epicondylitis of bilateral humerus
    # 312421000119107        └ Lateral epicondylitis of left humerus
    # 15636001000119108         └ Lateral epicondylitis of bilateral humerus

    with patch(
        "coding_systems.base.import_data_utils.call_command", mock_migrate_coding_system
    ):
        import_data(
            str(MOCK_SNOMEDCT_IMPORT_DATA_PATH),
            release_name="release SnomedCT 1",
            valid_from=date(2022, 10, 1),
            import_ref="Ref",
        )

    # A new CodingSystemRelease has been created
    assert CodingSystemRelease.objects.count() == cs_release_count + 1
    cs_release = CodingSystemRelease.objects.latest("id")
    assert cs_release.coding_system == "snomedct"
    assert cs_release.release_name == "release SnomedCT 1"
    assert cs_release.valid_from == date(2022, 10, 1)
    assert cs_release.import_ref == "Ref"

    assert cs_release.database_alias in settings.DATABASES
    concepts = Concept.objects.using(cs_release.database_alias).all()
    assert concepts.count() == 6
    assert set(concepts.values_list("id", flat=True)) == {
        "3723001",
        "439656005",
        "202855006",
        "312411000119100",
        "312421000119107",
        "15636001000119108",
    }
