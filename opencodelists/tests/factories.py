import factory

from opencodelists import actions
from opencodelists.models import Organisation, Project, User


class OrganisationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organisation

    name = "Test University"
    url = "https://test.ac.uk"

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override the default ``_create`` with our actions."""
        return actions.create_organisation(*args, **kwargs)


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    name = "Test Project"
    url = "https://test.org"
    details = "This is a test"

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override the default ``_create`` with our actions."""
        o = Organisation.objects.first() or OrganisationFactory()
        return actions.create_project(*args, organisations=[o], **kwargs)


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
