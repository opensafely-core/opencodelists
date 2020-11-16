import factory

from opencodelists import actions
from opencodelists.models import Organisation, User


class OrganisationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organisation

    name = factory.Sequence(lambda n: f"Test University {n}")
    url = "https://test.ac.uk"

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override the default ``_create`` with our actions."""
        organisation = actions.create_organisation(*args, **kwargs)

        # Create a user that belongs to the organisation, and assign this user to an
        # instance attribute.  This is useful in tests where we need to log a user in to
        # access an organisation's resources.
        organisation.regular_user = UserFactory()
        actions.add_user_to_organisation(
            user=organisation.regular_user,
            organisation=organisation,
            date_joined="2020-11-12",
        )
        return organisation


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.Sequence(lambda n: f"user{n}@example.com")
