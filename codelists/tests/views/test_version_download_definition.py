import csv
from io import StringIO


def test_get(client, version_with_excluded_codes):
    rsp = client.get(version_with_excluded_codes.get_download_definition_url())
    reader = csv.reader(StringIO(rsp.text))
    data = list(reader)
    assert data == [
        ["code", "term", "is_included"],
        ["156659008", "(Epicondylitis &/or tennis elbow) or (golfers' elbow)", "+"],
        ["128133004", "Disorder of elbow", "+"],
        ["439656005", "Arthritis of elbow", "-"],
    ]
