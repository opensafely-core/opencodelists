import pytest
from django.db import IntegrityError

from codelists import actions
from codelists.models import Codelist
from opencodelists.tests.assertions import assert_difference


def test_create_codelist(organisation):
    cl = actions.create_old_style_codelist(
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


def test_create_codelist_for_user(user):
    cl = actions.create_old_style_codelist(
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


def test_create_codelist_with_duplicate_name(organisation):
    actions.create_old_style_codelist(
        owner=organisation,
        name="Test",
        coding_system_id="snomedct",
        description="This is a test",
        methodology="This is how we did it",
        csv_data="code,description\n1067731000000107,Injury whilst swimming (disorder)",
    )

    with pytest.raises(IntegrityError):
        actions.create_old_style_codelist(
            owner=organisation,
            name="Test",
            coding_system_id="snomedct",
            description="This is a test",
            methodology="This is how we did it",
            csv_data="code,description\n1067731000000107,Injury whilst swimming (disorder)",
        )

    assert Codelist.objects.filter(handles__name="Test").count() == 1


def test_create_codelist_with_codes(user, disorder_of_elbow_excl_arthritis_codes):
    cl = actions.create_codelist_with_codes(
        owner=user,
        name="Test",
        coding_system_id="snomedct",
        codes=disorder_of_elbow_excl_arthritis_codes,
    )
    clv = cl.versions.get()
    assert len(clv.codes) == len(disorder_of_elbow_excl_arthritis_codes)

    code_to_status = {
        code_obj.code: code_obj.status for code_obj in clv.code_objs.all()
    }

    assert code_to_status == {
        "128133004": "+",  # Disorder of elbow
        "429554009": "(+)",  # Arthropathy of elbow
        "35185008": "(+)",  # Enthesopathy of elbow region
        "73583000": "(+)",  # Epicondylitis
        "239964003": "(+)",  # Soft tissue lesion of elbow region
        "439656005": "-",  # Arthritis of elbow
        "202855006": "(-)",  # Lateral epicondylitis
        "156659008": "+",  # (Epicondylitis &/or tennis elbow) ...
    }


def test_create_codelist_with_codes_with_metadata(
    user, disorder_of_elbow_excl_arthritis_codes
):
    cl = actions.create_codelist_with_codes(
        owner=user,
        name="Test",
        coding_system_id="snomedct",
        codes=disorder_of_elbow_excl_arthritis_codes,
        description="This is a test",
        methodology="This is how we did it",
        references=[{"text": "Some reference", "url": "http://example.com"}],
        signoffs=[{"user": user.username, "date": "2021-04-21"}],
    )
    assert cl.description == "This is a test"
    assert cl.methodology == "This is how we did it"
    assert cl.references.count() == 1
    assert cl.signoffs.count() == 1


def test_create_codelist_from_scratch(organisation, user):
    cl = actions.create_codelist_from_scratch(
        owner=organisation, name="Test", coding_system_id="snomedct", draft_owner=user
    )
    clv = cl.versions.get()
    assert clv.draft_owner == user


def test_create_version_with_codes(new_style_codelist):
    clv = actions.create_version_with_codes(
        codelist=new_style_codelist,
        codes={"128133004"},
        tag="test",
    )
    assert clv.codes == ("128133004",)
    assert clv.tag == "test"

    with pytest.raises(ValueError):
        actions.create_version_with_codes(
            codelist=new_style_codelist, codes={"128133004"}
        )

    with pytest.raises(ValueError):
        actions.create_version_with_codes(codelist=new_style_codelist, codes=set())


def test_create_version_from_ecl_expr(new_style_codelist):
    clv = actions.create_version_from_ecl_expr(
        codelist=new_style_codelist, expr="<<429554009", tag="test"
    )
    assert clv.codes == ("202855006", "429554009", "439656005")
    assert clv.tag == "test"

    clv = actions.create_version_from_ecl_expr(
        codelist=new_style_codelist, expr="<429554009"
    )
    assert clv.codes == ("202855006", "439656005")

    clv = actions.create_version_from_ecl_expr(
        codelist=new_style_codelist, expr="429554009"
    )
    assert clv.codes == ("429554009",)

    clv = actions.create_version_from_ecl_expr(
        codelist=new_style_codelist, expr="<<429554009 MINUS 202855006"
    )
    assert clv.codes == ("429554009", "439656005")


def test_publish_draft_version(version):
    actions.publish_version(version=version)
    version.refresh_from_db()


def test_convert_codelist_to_new_style(old_style_codelist, old_style_version):
    with assert_difference(old_style_codelist.versions.count, expected_difference=1):
        actions.convert_codelist_to_new_style(codelist=old_style_codelist)

    converted_version = old_style_codelist.versions.order_by("id").last()
    assert converted_version.csv_data is None
    assert old_style_version.codes == converted_version.codes


def test_export_to_builder(organisation_user, new_style_version):
    with assert_difference(
        new_style_version.codelist.versions.count, expected_difference=1
    ):
        draft = actions.export_to_builder(
            version=new_style_version, owner=organisation_user
        )

    assert draft.draft_owner == organisation_user
    assert draft.codes == new_style_version.codes
    assert draft.code_objs.count() == new_style_version.code_objs.count()
    assert draft.searches.count() == new_style_version.searches.count()
