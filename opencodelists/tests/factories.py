from opencodelists import actions
from opencodelists.models import Organisation, User


def create_organisation():
    return actions.create_organisation(name="Test University", url="https://test.ac.uk")


def create_project():
    o = Organisation.objects.first() or create_organisation()
    return actions.create_project(
        name="Test Project",
        url="https://test.org",
        details="This is a test",
        organisations=[o],
    )


def create_user():
    o = Organisation.objects.first() or create_organisation()
    return User.objects.create(name="Alice Apple", organisation=o)
