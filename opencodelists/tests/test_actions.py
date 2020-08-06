from opencodelists import actions

from .factories import OrganisationFactory


def test_create_organisation():
    o = actions.create_organisation(name="Test University", url="https://test.ac.uk")
    assert o.name == "Test University"
    assert o.slug == "test-university"
    assert o.url == "https://test.ac.uk"


def test_create_project():
    o = OrganisationFactory()
    p = actions.create_project(
        name="Test Project",
        url="https://test.org",
        details="This is a test",
        organisations=[o],
    )
    assert p.name == "Test Project"
    assert p.slug == "test-project"
    assert p.url == "https://test.org"
    assert p.details == "This is a test"
    assert list(p.organisations.all()) == [o]
