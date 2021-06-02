from codelists.presenters import present_search_results


def test_present_search_results(version_with_complete_searches):
    version = version_with_complete_searches
    code_to_term = version.coding_system.code_to_term(version.codeset.all_codes())
    results = present_search_results(version, code_to_term)
    assert [r["term_or_code"] for r in results] == [
        "arthritis",
        "elbow",
        "tennis",
        "code: 439656005",
    ]
    assert results[0] == {
        "term_or_code": "arthritis",
        "num_included": 2,
        "total": 3,
        "rows": [
            {"code": "3723001", "included": False, "term": "Arthritis"},
            {"code": "439656005", "included": True, "term": "Arthritis of elbow"},
            {"code": "202855006", "included": True, "term": "Lateral epicondylitis"},
        ],
    }
