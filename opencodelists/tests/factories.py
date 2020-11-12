import factory

from opencodelists import actions
from opencodelists.models import Organisation, User


class OrganisationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organisation

    name = "Test University"
    url = "https://test.ac.uk"

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override the default ``_create`` with our actions."""
        return actions.create_organisation(*args, **kwargs)


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.Sequence(lambda n: f"user{n}@example.com")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override the default ``_create`` with our actions."""
        o = Organisation.objects.first() or OrganisationFactory()
        return User.objects.create(organisation=o, **kwargs)
