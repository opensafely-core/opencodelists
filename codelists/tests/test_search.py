from codelists.coding_systems import CODING_SYSTEMS
from codelists.search import do_search


def test_do_search(snomedct_data):
    coding_system = CODING_SYSTEMS["snomedct"].most_recent()

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
        "156659008",  # (Epicondylitis &/or tennis elbow) ...
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
        "156659008",
    }

    assert search_results["ancestor_codes"] == {
        "116309007",  # Finding of elbow region
        "156659008",  # (Epicondylitis &/or tennis elbow) ...
    }
