from opencodelists import actions


def create_organisation():
    return actions.create_organisation(name="Test University", url="https://test.ac.uk")


def create_project():
    o = create_organisation()
    return actions.create_project(
        name="Test Project",
        url="https://test.org",
        details="This is a test",
        organisations=[o],
    )
