import datetime

import factory
import factory.fuzzy

from codelists import actions
from codelists.models import Reference, SignOff
from opencodelists.tests.factories import ProjectFactory


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


def create_codelist(csv_data=None):
    p = ProjectFactory()
    if csv_data is None:
        csv_data = (
            "code,description\n1067731000000107,Injury whilst swimming (disorder)"
        )

    return actions.create_codelist(
        project=p,
        name="Test Codelist",
        coding_system_id="snomedct",
        description="This is a test",
        methodology="This is how we did it",
        csv_data=csv_data,
    )


def create_draft_version():
    cl = create_codelist()
    return cl.versions.get()


def create_published_version():
    clv = create_draft_version()
    actions.publish_version(version=clv)
    return clv
