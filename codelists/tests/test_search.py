from pathlib import Path

from django.conf import settings
from django.core.management import call_command

from codelists.coding_systems import CODING_SYSTEMS
from codelists.search import do_search


def test_do_search():
    fixtures_path = Path(settings.BASE_DIR, "coding_systems", "snomedct", "fixtures")
    call_command("loaddata", fixtures_path / "core-model-components.json")
    call_command("loaddata", fixtures_path / "tennis-elbow.json")
    coding_system = CODING_SYSTEMS["snomedct"]

    search_results = do_search(coding_system, "elbow")

    assert search_results["all_codes"] == {
        "116309007",  # Finding of elbow region
        "128133004",  # Disorder of elbow
        "239964003",  # Soft tissue lesion of elbow region
        "35185008",  # Enthesopathy of elbow region
        "73583000",  # Epicondylitis
        "202855006",  # Lateral epicondylitis
        "429554009",  # Arthropathy of elbow
        "439656005",  # Arthritis of elbow
        "298869002",  # Finding of elbow joint
        "298163003",  # Elbow joint inflamed
    }

    assert search_results["matching_codes"] == {
        # Everything above, except Epicondylitis
        "116309007",
        "128133004",
        "239964003",
        "35185008",
        "202855006",
        "429554009",
        "439656005",
        "298869002",
        "298163003",
    }

    assert search_results["ancestor_codes"] == {"116309007"}  # Finding of elbow region
