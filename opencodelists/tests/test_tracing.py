def test_user_span_attribute_added_for_logged_in_user(
    client, user_without_organisation, span_exporter
):
    client.force_login(user_without_organisation)

    client.get("/")
    spans = span_exporter.get_finished_spans()

    assert spans[0].attributes.get("user") == "dave"


def test_user_span_attribute_added_for_non_logged_in_user(
    client, user_without_organisation, span_exporter
):
    client.get("/")
    spans = span_exporter.get_finished_spans()

    assert spans[0].attributes.get("user") == ""
