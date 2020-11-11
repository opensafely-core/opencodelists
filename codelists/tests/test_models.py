def test_old_style_codes(tennis_elbow_codelist):
    cl = tennis_elbow_codelist
    clv = cl.versions.get()
    assert clv.codes == (
        "128133004",
        "202855006",
        "239964003",
        "35185008",
        "429554009",
        "439656005",
        "73583000",
    )


def test_old_style_table(tennis_elbow_codelist):
    cl = tennis_elbow_codelist
    clv = cl.versions.get()
    assert clv.table == [
        ["id", "name"],
        ["429554009", "Arthropathy of elbow (disorder)"],
        ["128133004", "Disorder of elbow (disorder)"],
        ["202855006", "Lateral epicondylitis (disorder)"],
        ["439656005", "Arthritis of elbow (disorder)"],
        ["73583000", "Epicondylitis (disorder)"],
        ["35185008", "Enthesopathy of elbow region (disorder)"],
        ["239964003", "Soft tissue lesion of elbow region (disorder)"],
    ]


def test_new_style_codes(tennis_elbow_new_style_codelist):
    cl = tennis_elbow_new_style_codelist
    clv = cl.versions.get()
    assert clv.codes == (
        "128133004",
        "202855006",
        "239964003",
        "35185008",
        "429554009",
        "439656005",
        "73583000",
    )


def test_new_style_table(tennis_elbow_new_style_codelist):
    cl = tennis_elbow_new_style_codelist
    clv = cl.versions.get()
    assert clv.table == [
        ["code", "term"],
        ["128133004", "Disorder of elbow"],
        ["202855006", "Lateral epicondylitis"],
        ["239964003", "Soft tissue lesion of elbow region"],
        ["35185008", "Enthesopathy of elbow region"],
        ["429554009", "Arthropathy of elbow"],
        ["439656005", "Arthritis of elbow"],
        ["73583000", "Epicondylitis"],
    ]
