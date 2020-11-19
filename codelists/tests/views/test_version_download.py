import csv
from io import StringIO

from ..factories import create_draft_version, create_published_version


def test_get_published(client):
    clv = create_published_version()
    cl = clv.codelist
    rsp = client.get(
        f"/codelist/{cl.organisation.slug}/{cl.slug}/{clv.tag}/download.csv"
    )
    reader = csv.reader(StringIO(rsp.content.decode("utf8")))
    data = list(reader)
    assert data[0] == ["code", "description"]
    assert data[1] == ["1067731000000107", "Injury whilst swimming (disorder)"]


def test_get_published_with_draft_url(client):
    clv = create_published_version()
    cl = clv.codelist
    rsp = client.get(
        f"/codelist/{cl.organisation.slug}/{cl.slug}/{clv.tag}-draft/download.csv"
    )
    assert rsp.status_code == 404


def test_get_draft(client):
    clv = create_draft_version()
    cl = clv.codelist
    rsp = client.get(
        f"/codelist/{cl.organisation.slug}/{cl.slug}/{clv.tag}-draft/download.csv"
    )
    reader = csv.reader(StringIO(rsp.content.decode("utf8")))
    data = list(reader)
    assert data[0] == ["code", "description"]
    assert data[1] == ["1067731000000107", "Injury whilst swimming (disorder)"]


def test_get_draft_with_published_url(client):
    clv = create_draft_version()
    cl = clv.codelist
    rsp = client.get(
        f"/codelist/{cl.organisation.slug}/{cl.slug}/{clv.tag}/download.csv"
    )
    assert rsp.status_code == 404
