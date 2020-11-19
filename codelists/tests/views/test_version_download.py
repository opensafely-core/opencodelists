import csv
from io import StringIO

from ..factories import create_published_version


def test_get(client):
    clv = create_published_version()
    rsp = client.get(clv.get_download_url())
    reader = csv.reader(StringIO(rsp.content.decode("utf8")))
    data = list(reader)
    assert data[0] == ["code", "description"]
    assert data[1] == ["1067731000000107", "Injury whilst swimming (disorder)"]
