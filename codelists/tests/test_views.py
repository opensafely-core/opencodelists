import csv
from io import BytesIO, StringIO

import pytest
from pytest_django.asserts import assertContains, assertRedirects

from . import factories

pytestmark = pytest.mark.freeze_time("2020-07-23")


def test_create_codelist(client):
    p = factories.create_project()
    csv_data = "code,description\n1067731000000107,Injury whilst swimming (disorder)"
    data = {
        "name": "Test Codelist",
        "coding_system_id": "snomedct",
        "description": "This is a test",
        "methodology": "This is how we did it",
        "csv_data": _build_file_for_upload(csv_data),
    }
    rsp = client.post(f"/codelist/{p.slug}/", data, follow=True)
    assertRedirects(rsp, f"/codelist/{p.slug}/test-codelist/2020-07-23/")


def test_codelist(client):
    cl = factories.create_codelist()
    clv = cl.versions.get()
    rsp = client.get(f"/codelist/{cl.project.slug}/{cl.slug}/", follow=True)
    assertRedirects(rsp, f"/codelist/{cl.project.slug}/{cl.slug}/{clv.version_str}/")
    assertContains(rsp, cl.name)


def test_version(client):
    cl = factories.create_codelist()
    clv = cl.versions.get()
    rsp = client.get(f"/codelist/{cl.project.slug}/{cl.slug}/{clv.version_str}/")
    assertContains(rsp, cl.name)
    assertContains(rsp, cl.description)
    assertContains(rsp, cl.methodology)


def test_download(client):
    cl = factories.create_codelist()
    clv = cl.versions.get()
    rsp = client.get(
        f"/codelist/{cl.project.slug}/{cl.slug}/{clv.version_str}/download.csv"
    )
    reader = csv.reader(StringIO(rsp.content.decode("utf8")))
    data = list(reader)
    assert data[0] == ["code", "description"]
    assert data[1] == ["1067731000000107", "Injury whilst swimming (disorder)"]


def test_create_version(client):
    cl = factories.create_codelist()
    csv_data = "code,description\n1068181000000106, Injury whilst synchronised swimming (disorder)"
    data = {
        "csv_data": _build_file_for_upload(csv_data),
    }
    rsp = client.post(f"/codelist/{cl.project.slug}/{cl.slug}/", data, follow=True)
    assertRedirects(rsp, f"/codelist/{cl.project.slug}/{cl.slug}/2020-07-23-a/")


def _build_file_for_upload(contents):
    buffer = BytesIO()
    buffer.write(contents.encode("utf8"))
    buffer.seek(0)
    return buffer
