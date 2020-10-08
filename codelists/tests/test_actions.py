import pytest
from django.db import IntegrityError

from codelists import actions
from codelists.models import Codelist
from opencodelists.tests.factories import ProjectFactory

from . import factories

pytestmark = pytest.mark.freeze_time("2020-07-23")


def test_create_codelist():
    p = ProjectFactory()
    cl = actions.create_codelist(
        project=p,
        name="Test Codelist",
        coding_system_id="snomedct",
        description="This is a test",
        methodology="This is how we did it",
        csv_data="code,description\n1067731000000107,Injury whilst swimming (disorder)",
    )
    assert cl.project == p
    assert cl.name == "Test Codelist"
    assert cl.slug == "test-codelist"
    assert cl.coding_system_id == "snomedct"
    assert cl.description == "This is a test"
    assert cl.methodology == "This is how we did it"
    assert cl.versions.count() == 1
    clv = cl.versions.get()
    assert clv.version_str == "2020-07-23"
    assert "whilst swimming" in clv.csv_data


def test_create_codelist_with_duplicate_name():
    p = ProjectFactory()

    actions.create_codelist(
        project=p,
        name="Test",
        coding_system_id="snomedct",
        description="This is a test",
        methodology="This is how we did it",
        csv_data="code,description\n1067731000000107,Injury whilst swimming (disorder)",
    )

    with pytest.raises(IntegrityError):
        actions.create_codelist(
            project=p,
            name="Test",
            coding_system_id="snomedct",
            description="This is a test",
            methodology="This is how we did it",
            csv_data="code,description\n1067731000000107,Injury whilst swimming (disorder)",
        )

    assert Codelist.objects.count() == 1


def test_create_version_on_same_day():
    cl = factories.CodelistFactory()
    clv = actions.create_version(
        codelist=cl,
        csv_data="code,description\n1068181000000106, Injury whilst synchronised swimming (disorder)",
    )
    assert clv.version_str == "2020-07-23-a"
    assert "whilst synchronised swimming" in clv.csv_data
    assert cl.versions.count() == 2


def test_create_version_on_next_day(freezer):
    cl = factories.CodelistFactory()
    freezer.move_to("2020-07-24")
    clv = actions.create_version(
        codelist=cl,
        csv_data="code,description\n1068181000000106, Injury whilst synchronised swimming (disorder)",
    )
    assert clv.version_str == "2020-07-24"
    assert "whilst synchronised swimming" in clv.csv_data
    assert cl.versions.count() == 2


def test_update_draft_version():
    clv = factories.create_draft_version()
    actions.update_version(
        version=clv,
        csv_data="code,description\n1068181000000106, Injury whilst synchronised swimming (disorder)",
    )
    clv.refresh_from_db()
    assert "whilst synchronised swimming" in clv.csv_data
    assert clv.codelist.versions.count() == 1


def test_update_published_version():
    clv = factories.create_published_version()
    with pytest.raises(AssertionError):
        actions.update_version(
            version=clv,
            csv_data="code,description\n1068181000000106, Injury whilst synchronised swimming (disorder)",
        )


def test_publish_draft_version():
    clv = factories.create_draft_version()
    actions.publish_version(version=clv)
    clv.refresh_from_db()
    assert not clv.is_draft


def test_publish_published_version():
    clv = factories.create_published_version()
    with pytest.raises(AssertionError):
        actions.publish_version(version=clv)
