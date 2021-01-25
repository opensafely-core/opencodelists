from codelists.views.version_diff import summarise


def test_get(client, version_with_no_searches, version_with_some_searches):
    rsp = client.get(version_with_no_searches.get_diff_url(version_with_some_searches))
    assert rsp.status_code == 200

    rsp = client.get(version_with_some_searches.get_diff_url(version_with_no_searches))
    assert rsp.status_code == 200


def test_summarise(version_with_no_searches, version_with_some_searches):
    lhs_codes = set(version_with_no_searches.codes)
    rhs_codes = set(version_with_some_searches.codes)
    rhs_only_codes = rhs_codes - lhs_codes
    assert summarise(rhs_only_codes, version_with_no_searches.coding_system) == [
        {
            "code": "439656005",
            "descendants": [{"code": "202855006", "term": "Lateral epicondylitis"}],
            "term": "Arthritis of elbow",
        }
    ]
