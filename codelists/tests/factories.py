import datetime

import factory
import factory.fuzzy

from codelists import actions
from codelists.models import Codelist, Reference, SignOff
from opencodelists.tests.factories import UserFactory


class CodelistFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Codelist

    owner = factory.SubFactory("opencodelists.tests.factories.OrganisationFactory")

    name = "Test Codelist"
    coding_system_id = "snomedct"
    description = "This is a test"
    methodology = "This is how we did it"
    csv_data = "code,description\n1067731000000107,Injury whilst swimming (disorder)"

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override the default ``_create`` with our actions."""
        return actions.create_codelist(*args, **kwargs)


class ReferenceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Reference

    text = factory.Sequence(lambda n: f"Reference {n}")
    url = factory.Sequence(lambda n: f"http://example.com/{n}")


class SignOffFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SignOff

    user = factory.SubFactory("opencodelists.tests.factories.UserFactory")
    date = factory.fuzzy.FuzzyDate(datetime.date(2020, 1, 1))


def create_draft_version():
    codelist = CodelistFactory()
    return codelist.versions.get()


def create_published_version():
    clv = create_draft_version()
    actions.publish_version(version=clv)
    return clv


def create_published_version_for_user():
    codelist = CodelistFactory(owner=UserFactory())
    clv = codelist.versions.get()
    actions.publish_version(version=clv)
    return clv
