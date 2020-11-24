import pytest
from django.db import IntegrityError

from codelists import actions
from codelists.models import Codelist
from opencodelists.tests.factories import OrganisationFactory, UserFactory

from . import factories

pytestmark = pytest.mark.freeze_time("2020-07-23")


def test_create_codelist():
    organisation = OrganisationFactory()
    cl = actions.create_codelist(
        owner=organisation,
        name="Test Codelist",
        coding_system_id="snomedct",
        description="This is a test",
        methodology="This is how we did it",
        csv_data="code,description\n1067731000000107,Injury whilst swimming (disorder)",
    )
    assert cl.organisation == organisation
    assert cl.user is None
    assert cl.name == "Test Codelist"
    assert cl.slug == "test-codelist"
    assert cl.coding_system_id == "snomedct"
    assert cl.description == "This is a test"
    assert cl.methodology == "This is how we did it"
    assert cl.versions.count() == 1
    clv = cl.versions.get()
    assert "whilst swimming" in clv.csv_data


def test_create_codelist_for_user():
    user = UserFactory()
    cl = actions.create_codelist(
        owner=user,
        name="Test Codelist",
        coding_system_id="snomedct",
        description="This is a test",
        methodology="This is how we did it",
        csv_data="code,description\n1067731000000107,Injury whilst swimming (disorder)",
    )
    assert cl.organisation is None
    assert cl.user == user
    assert cl.name == "Test Codelist"
    assert cl.slug == "test-codelist"
    assert cl.coding_system_id == "snomedct"
    assert cl.description == "This is a test"
    assert cl.methodology == "This is how we did it"
    assert cl.versions.count() == 1
    clv = cl.versions.get()
    assert "whilst swimming" in clv.csv_data


def test_create_codelist_with_duplicate_name():
    organisation = OrganisationFactory()

    actions.create_codelist(
        owner=organisation,
        name="Test",
        coding_system_id="snomedct",
        description="This is a test",
        methodology="This is how we did it",
        csv_data="code,description\n1067731000000107,Injury whilst swimming (disorder)",
    )

    with pytest.raises(IntegrityError):
        actions.create_codelist(
            owner=organisation,
            name="Test",
            coding_system_id="snomedct",
            description="This is a test",
            methodology="This is how we did it",
            csv_data="code,description\n1067731000000107,Injury whilst swimming (disorder)",
        )

    assert Codelist.objects.filter(name="Test").count() == 1


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


def test_convert_codelist_to_new_style(tennis_elbow_codelist):
    cl = tennis_elbow_codelist
    original_clv = cl.versions.get()

    actions.convert_codelist_to_new_style(codelist=cl)

    assert cl.versions.count() == 2
    converted_clv = cl.versions.last()
    assert converted_clv.csv_data is None
    assert original_clv.codes == converted_clv.codes
