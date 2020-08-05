from codelists import actions
from opencodelists.tests.factories import ProjectFactory


def create_codelist():
    p = ProjectFactory()
    return actions.create_codelist(
        project=p,
        name="Test Codelist",
        coding_system_id="snomedct",
        description="This is a test",
        methodology="This is how we did it",
        csv_data="code,description\n1067731000000107,Injury whilst swimming (disorder)",
    )


def create_draft_version():
    cl = create_codelist()
    return cl.versions.get()


def create_published_version():
    clv = create_draft_version()
    actions.publish_version(version=clv)
    return clv
