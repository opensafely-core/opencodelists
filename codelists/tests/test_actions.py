import pytest
from django.db import IntegrityError
from django.db.models.fields import reverse_related

from codelists import actions
from codelists.coding_systems import most_recent_database_alias
from codelists.models import (
    CachedHierarchy,
    Codelist,
    CodelistVersion,
    CodeObj,
    Search,
    SearchResult,
    Status,
)
from mappings.bnfdmd.models import Mapping as BnfDmdMapping
from opencodelists.tests.assertions import assert_difference, assert_no_difference


def test_create_codelist(organisation):
    cl = actions.create_old_style_codelist(
        owner=organisation,
        name="Test Codelist",
        coding_system_id="snomedct",
        coding_system_database_alias=most_recent_database_alias("snomedct"),
        description="This is a test",
        methodology="This is how we did it",
        # 239964003 is actually the code for "Soft tissue lesion of elbow region"
        # The action validates that all codes are present in the coding system,
        # but doesn't check terms match
        csv_data="code,description\n239964003,Injury whilst swimming (disorder)",
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
    assert clv.is_under_review


def test_create_codelist_for_user(user):
    cl = actions.create_old_style_codelist(
        owner=user,
        name="Test Codelist",
        coding_system_id="snomedct",
        coding_system_database_alias=most_recent_database_alias("snomedct"),
        description="This is a test",
        methodology="This is how we did it",
        csv_data="code,description\n239964003,Injury whilst swimming (disorder)",
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
        coding_system_database_alias=most_recent_database_alias("snomedct"),
        description="This is a test",
        methodology="This is how we did it",
        csv_data="code,description\n239964003,Injury whilst swimming (disorder)",
    )

    with pytest.raises(IntegrityError):
        actions.create_old_style_codelist(
            owner=organisation,
            name="Test",
            coding_system_id="snomedct",
            coding_system_database_alias=most_recent_database_alias("snomedct"),
            description="This is a test",
            methodology="This is how we did it",
            csv_data="code,description\n239964003,Injury whilst swimming (disorder)",
        )

    assert Codelist.objects.filter(handles__name="Test").count() == 1


def test_create_codelist_with_codes(user, disorder_of_elbow_excl_arthritis_codes):
    cl = actions.create_codelist_with_codes(
        owner=user,
        name="Test",
        coding_system_id="snomedct",
        coding_system_database_alias=most_recent_database_alias("snomedct"),
        codes=disorder_of_elbow_excl_arthritis_codes,
    )
    clv = cl.versions.get()
    assert clv.is_draft
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
        coding_system_database_alias=most_recent_database_alias("snomedct"),
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


def test_create_or_update_codelist_create(user, disorder_of_elbow_excl_arthritis_codes):
    cl = actions.create_or_update_codelist(
        owner=user,
        name="Test",
        coding_system_id="snomedct",
        coding_system_database_alias=most_recent_database_alias("snomedct"),
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
    assert cl.versions.count() == 1
    clv = cl.versions.get()
    assert clv.codes == tuple(sorted(disorder_of_elbow_excl_arthritis_codes))


def test_create_or_update_codelist_update(
    organisation, codelist, disorder_of_elbow_excl_arthritis_codes
):
    with assert_difference(codelist.versions.count, expected_difference=1):
        actions.create_or_update_codelist(
            owner=organisation,
            name=codelist.name,
            coding_system_id="snomedct",
            coding_system_database_alias=most_recent_database_alias("snomedct"),
            codes=disorder_of_elbow_excl_arthritis_codes,
            description="This is a test (updated)",
            methodology="This is how we did it (updated)",
        )

    codelist.refresh_from_db()
    assert codelist.description == "This is a test (updated)"
    assert codelist.methodology == "This is how we did it (updated)"
    clv = codelist.versions.order_by("id").last()
    assert clv.status == "under review"
    assert clv.codes == tuple(sorted(disorder_of_elbow_excl_arthritis_codes))


def test_create_version_with_forced_publish(
    organisation, codelist, disorder_of_elbow_excl_arthritis_codes
):
    actions.create_or_update_codelist(
        owner=organisation,
        name=codelist.name,
        coding_system_id="snomedct",
        coding_system_database_alias=most_recent_database_alias("snomedct"),
        codes=disorder_of_elbow_excl_arthritis_codes,
        should_publish=True,
    )

    clv = codelist.versions.order_by("id").last()
    assert clv.status == "published"


def test_create_or_update_codelist_update_no_change_to_codes(
    organisation, codelist, disorder_of_elbow_codes
):
    with assert_no_difference(codelist.versions.count):
        actions.create_or_update_codelist(
            owner=organisation,
            name=codelist.name,
            coding_system_id="snomedct",
            coding_system_database_alias=most_recent_database_alias("snomedct"),
            codes=disorder_of_elbow_codes,
            description="This is a test (updated)",
            methodology="This is how we did it (updated)",
        )

    codelist.refresh_from_db()
    assert codelist.description == "This is a test (updated)"
    assert codelist.methodology == "This is how we did it (updated)"


def test_create_or_update_codelist_update_no_change_to_codes_with_force(
    user, organisation, disorder_of_elbow_codes
):
    new_codelist_name = "test versions"
    cl = actions.create_or_update_codelist(
        owner=organisation,
        name=new_codelist_name,
        coding_system_id="snomedct",
        coding_system_database_alias=most_recent_database_alias("snomedct"),
        codes=disorder_of_elbow_codes,
        description="This is a test",
        methodology="This is how we did it",
        references=[{"text": "Some reference", "url": "http://example.com"}],
        signoffs=[{"user": user.username, "date": "2021-04-21"}],
    )

    with assert_difference(cl.versions.count, expected_difference=1):
        actions.create_or_update_codelist(
            owner=organisation,
            name=new_codelist_name,
            coding_system_id="snomedct",
            coding_system_database_alias=most_recent_database_alias("snomedct"),
            codes=disorder_of_elbow_codes,
            description="This is a test (updated)",
            methodology="This is how we did it (updated)",
            always_create_new_version=True,
        )


def test_create_or_update_codelist_update_no_change_to_codes_without_force(
    user, organisation, disorder_of_elbow_codes
):
    new_codelist_name = "test versions false"
    cl = actions.create_or_update_codelist(
        owner=organisation,
        name=new_codelist_name,
        coding_system_id="snomedct",
        coding_system_database_alias=most_recent_database_alias("snomedct"),
        codes=disorder_of_elbow_codes,
        description="This is a test",
        methodology="This is how we did it",
        references=[{"text": "Some reference", "url": "http://example.com"}],
        signoffs=[{"user": user.username, "date": "2021-04-21"}],
    )

    with assert_no_difference(cl.versions.count):
        actions.create_or_update_codelist(
            owner=organisation,
            name=new_codelist_name,
            coding_system_id="snomedct",
            coding_system_database_alias=most_recent_database_alias("snomedct"),
            codes=disorder_of_elbow_codes,
            description="This is a test (updated)",
            methodology="This is how we did it (updated)",
            always_create_new_version=False,
        )


def test_create_codelist_from_scratch(organisation, user):
    cl = actions.create_codelist_from_scratch(
        owner=organisation,
        name="Test",
        coding_system_id="snomedct",
        coding_system_database_alias=most_recent_database_alias("snomedct"),
        author=user,
    )
    clv = cl.versions.get()
    assert clv.author == user
    assert clv.is_draft


def test_create_version_with_codes(new_style_codelist):
    clv = actions.create_version_with_codes(
        codelist=new_style_codelist,
        coding_system_database_alias=most_recent_database_alias("snomedct"),
        codes={"128133004"},
        tag="test",
    )
    assert clv.codes == ("128133004",)
    assert clv.tag == "test"
    assert clv.is_under_review

    clv = actions.create_version_with_codes(
        codelist=new_style_codelist,
        coding_system_database_alias=most_recent_database_alias("snomedct"),
        codes={"128133004"},
    )
    assert clv is None

    with pytest.raises(ValueError):
        actions.create_version_with_codes(
            codelist=new_style_codelist,
            coding_system_database_alias=most_recent_database_alias("snomedct"),
            codes=set(),
        )


def test_create_version_from_ecl_expr(new_style_codelist):
    clv = actions.create_version_from_ecl_expr(
        codelist=new_style_codelist,
        coding_system_database_alias=most_recent_database_alias("snomedct"),
        expr="<<429554009",
        tag="test",
    )
    assert clv.codes == ("202855006", "429554009", "439656005")
    assert clv.tag == "test"
    assert clv.is_under_review

    clv = actions.create_version_from_ecl_expr(
        codelist=new_style_codelist,
        coding_system_database_alias=most_recent_database_alias("snomedct"),
        expr="<429554009",
    )
    assert clv.codes == ("202855006", "439656005")

    clv = actions.create_version_from_ecl_expr(
        codelist=new_style_codelist,
        coding_system_database_alias=most_recent_database_alias("snomedct"),
        expr="429554009",
    )
    assert clv.codes == ("429554009",)

    clv = actions.create_version_from_ecl_expr(
        codelist=new_style_codelist,
        coding_system_database_alias=most_recent_database_alias("snomedct"),
        expr="<<429554009 MINUS 202855006",
    )
    assert clv.codes == ("429554009", "439656005")


def test_update_codelist_unchanged_handle(
    codelist, organisation_user, organisation_admin
):
    # This test verifies that we can update a codelist without changing its handle.  It
    # verifies that all other fields are updated as expected.

    updated_references = [
        {"text": "Reference 1 updated", "url": "https://example.com/reference1"},
        {"text": "Reference 3", "url": "https://example.com/reference3"},
    ]
    updated_signoffs = [
        {"user": organisation_user, "date": "2020-03-29"},
        {"user": organisation_admin, "date": "2020-03-30"},
    ]
    actions.update_codelist(
        codelist=codelist,
        owner=codelist.owner,
        name=codelist.name,
        slug=codelist.slug,
        description="updated description",
        methodology="updated methodology",
        references=updated_references,
        signoffs=updated_signoffs,
    )

    assert codelist.handles.count() == 1
    assert codelist.description == "updated description"
    assert codelist.methodology == "updated methodology"
    assert (
        list(codelist.references.order_by("url").values("text", "url"))
        == updated_references
    )
    assert [
        {"user": signoff.user, "date": str(signoff.date)}
        for signoff in codelist.signoffs.order_by("date")
    ] == updated_signoffs


def test_update_codelist_new_handle(codelist, user):
    # This test verifies that we can update a codelist's owner, name, and slug.  Doing
    # so creates a new handle.
    actions.update_codelist(
        codelist=codelist,
        owner=user,
        name="New name",
        slug="new-slug",
        description=codelist.description,
        methodology=codelist.methodology,
        references=[],
        signoffs=[],
    )

    # codelist.refresh_from_db() isn't enough here -- we need to clear the cached
    # current_handle property.
    codelist = Codelist.objects.get(pk=codelist.pk)

    assert codelist.handles.count() == 2
    assert codelist.owner == user
    assert codelist.name == "New name"
    assert codelist.slug == "new-slug"


def test_update_codelist_old_handle(codelist, user):
    # This test verifies that we can revert a codelist's owner, name, and slug to
    # earlier values.  Doing so does not create a new handle.
    orig_owner = codelist.owner
    orig_name = codelist.name
    orig_slug = codelist.slug

    actions.update_codelist(
        codelist=codelist,
        owner=user,
        name="New name",
        slug="new-slug",
        description=codelist.description,
        methodology=codelist.methodology,
        references=[],
        signoffs=[],
    )

    # codelist.refresh_from_db() isn't enough here -- we need to clear the cached
    # current_handle property.
    codelist = Codelist.objects.get(pk=codelist.pk)

    actions.update_codelist(
        codelist=codelist,
        owner=orig_owner,
        name=orig_name,
        slug=orig_slug,
        description=codelist.description,
        methodology=codelist.methodology,
        references=[],
        signoffs=[],
    )

    codelist = Codelist.objects.get(pk=codelist.pk)

    assert codelist.handles.count() == 2
    assert codelist.owner == orig_owner
    assert codelist.name == orig_name
    assert codelist.slug == orig_slug


def test_update_codelist_duplicate_slug(new_style_codelist, old_style_codelist):
    # This test verifies that the correct error is raised when trying to update
    # the slug of a codelist to the slug of another codelist with the same
    # owner.

    with pytest.raises(actions.DuplicateHandleError) as e:
        actions.update_codelist(
            codelist=new_style_codelist,
            owner=new_style_codelist.owner,
            name=new_style_codelist.name,
            slug=old_style_codelist.slug,
            description=new_style_codelist.description,
            methodology=new_style_codelist.methodology,
            references=[],
            signoffs=[],
        )

    assert e._excinfo[1].field == "slug"


def test_update_codelist_duplicate_name(new_style_codelist, old_style_codelist):
    # This test verifies that the correct error is raised when trying to update
    # the name of a codelist to the name of another codelist with the same
    # owner.

    with pytest.raises(actions.DuplicateHandleError) as e:
        actions.update_codelist(
            codelist=new_style_codelist,
            owner=new_style_codelist.owner,
            name=old_style_codelist.name,
            slug=new_style_codelist.slug,
            description=new_style_codelist.description,
            methodology=new_style_codelist.methodology,
            references=[],
            signoffs=[],
        )

    assert e._excinfo[1].field == "name"


def test_publish(version_under_review):
    # The codelist has one published version and two versions under review.  When we
    # publish one of the versions under review, we expect the other one to be deleted.

    codelist = version_under_review.codelist

    with assert_difference(codelist.versions.count, expected_difference=-1):
        actions.publish_version(version=version_under_review)

    version_under_review.refresh_from_db()
    assert version_under_review.is_published


def test_delete_version(old_style_codelist):
    # Verify that delete_version deletes the given version, and that when the last
    # remaining version is deleted, the codelist is too.

    codelist = old_style_codelist
    codelist_pk = codelist.pk
    version1, version2 = codelist.versions.order_by("id")

    codelist_was_deleted = actions.delete_version(version=version2)
    assert not codelist_was_deleted
    assert codelist.versions.count() == 1

    codelist_was_deleted = actions.delete_version(version=version1)
    assert codelist_was_deleted
    assert not CodelistVersion.objects.filter(codelist_id=codelist_pk).exists()
    assert not Codelist.objects.filter(pk=codelist_pk).exists()


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
            version=new_style_version,
            author=organisation_user,
            coding_system_database_alias=most_recent_database_alias("snomedct"),
        )

    assert draft.author == organisation_user
    assert draft.codes == new_style_version.codes
    assert draft.code_objs.count() == new_style_version.code_objs.count()
    assert draft.searches.count() == new_style_version.searches.count()


def test_export_to_builder_unknown_codes(organisation_user, new_style_version):
    # delete a CodeObj that's included by a parent from the version to simulate a new concept
    # in the coding system
    missing_implicit_concept = new_style_version.code_objs.filter(status="(+)").first()
    missing_implicit_concept.delete()

    with assert_difference(
        new_style_version.codelist.versions.count, expected_difference=1
    ):
        draft = actions.export_to_builder(
            version=new_style_version,
            author=organisation_user,
            coding_system_database_alias=most_recent_database_alias("snomedct"),
        )
    # The newly created draft has one additional code obj (the one we deleted)
    assert draft.code_objs.count() == new_style_version.code_objs.count() + 1
    new_code = draft.code_objs.get(code=missing_implicit_concept.code)
    assert new_code.status == "?"
    assert draft.searches.count() == new_style_version.searches.count()


def test_add_codelist_tag(codelist):
    actions.add_codelist_tag(codelist=codelist, tag="TAG")

    assert Codelist.objects.get(tags__name="TAG") == codelist


def test_convert_bnf_codelist_version_to_dmd(bnf_version_asthma, dmd_bnf_mapping_data):
    assert len(bnf_version_asthma.codes) == 3
    # dmd_data contains mappings for the 2 BNF codes and one extra
    assert BnfDmdMapping.objects.count() == 3

    dmd_codelist = actions.convert_bnf_codelist_version_to_dmd(bnf_version_asthma)
    # New dmd codelist is created with "-dmd" appended to name and slug
    assert dmd_codelist.coding_system_id == "dmd"
    assert dmd_codelist.name == f"{bnf_version_asthma.codelist.name} - dmd"
    assert dmd_codelist.slug == f"{bnf_version_asthma.codelist.slug}-dmd"
    # References are duplicated from the original
    assert dmd_codelist.references.count() == 2
    assert {
        (ref.text, ref.url) for ref in bnf_version_asthma.codelist.references.all()
    } == {(ref.text, ref.url) for ref in dmd_codelist.references.all()}
    # original version url in methodology
    assert bnf_version_asthma.get_absolute_url() in dmd_codelist.methodology

    assert dmd_codelist.versions.count() == 1
    dmd_version = dmd_codelist.versions.first()

    # status is under review by default
    assert dmd_version.status == "under review"
    assert dmd_version.csv_data == (
        "dmd_type,dmd_id,dmd_name,bnf_code\n"
        "VMP,10514511000001106,Adrenaline (base) 220micrograms/dose inhaler,0301012A0AAABAB\n"
        "VMP,10525011000001107,Adrenaline (base) 220micrograms/dose inhaler refill,0301012A0AAACAC\n"
    )


def test_cannot_convert_non_bnf_codelist_to_dmd(version):
    assert version.coding_system_id == "snomedct"
    with pytest.raises(AssertionError):
        actions.convert_bnf_codelist_version_to_dmd(version)


def test_cannot_create_duplicate_converted_dmd_codelist(
    bnf_version_asthma, dmd_bnf_mapping_data
):
    # convert once to create the new codelist
    actions.convert_bnf_codelist_version_to_dmd(bnf_version_asthma)
    # attempt to convert again
    with pytest.raises(IntegrityError):
        actions.convert_bnf_codelist_version_to_dmd(bnf_version_asthma)


def test_can_update_converted_dmd_codelist(bnf_version_asthma, dmd_bnf_mapping_data):
    # convert once to create the new codelist
    dmd_codelist = actions.convert_bnf_codelist_version_to_dmd(bnf_version_asthma)
    assert dmd_codelist.versions.count() == 1

    # convert again with modified BNF codes
    bnf_version_asthma.codes += ("0301011R0AAADAD",)
    actions.convert_bnf_codelist_version_to_dmd(bnf_version_asthma)

    assert dmd_codelist.versions.count() == 2
    dmd_version = dmd_codelist.versions.last()

    # status is under review by default
    assert dmd_version.status == "under review"
    assert dmd_version.csv_data == (
        "dmd_type,dmd_id,dmd_name,bnf_code\n"
        "VMP,35936411000001109,Salbutamol 100micrograms/dose breath actuated inhaler,0301011R0AAADAD\n"
        "VMP,10514511000001106,Adrenaline (base) 220micrograms/dose inhaler,0301012A0AAABAB\n"
        "VMP,10525011000001107,Adrenaline (base) 220micrograms/dose inhaler refill,0301012A0AAACAC\n"
    )


def test_create_with_unfound_codes(new_style_codelist):
    # Error is raised if any of the codes are not found in the coding system
    db_alias = most_recent_database_alias("snomedct")
    unfound_code = "999999999"
    with pytest.raises(ValueError) as exc_info:
        actions.create_version_with_codes(
            codelist=new_style_codelist,
            coding_system_database_alias=db_alias,
            codes={unfound_code},
            tag="test",
        )

    assert "Attempting to import codes that aren't in" in str(exc_info.value)
    assert db_alias in str(exc_info.value)
    assert unfound_code in str(exc_info.value)


def test_create_with_unfound_codes_no_error(new_style_codelist):
    # No error is raised if the codes are not found in the coding system, but
    # a note is added to the description
    unfound_code = "999999999"
    clv = actions.create_version_with_codes(
        codelist=new_style_codelist,
        coding_system_database_alias=most_recent_database_alias("snomedct"),
        codes={unfound_code},
        tag="test",
        ignore_unfound_codes=True,
    )
    assert clv.codes == ()
    assert unfound_code in clv.codelist.description


def test_update_codelist_change_slug(
    organisation, codelist, disorder_of_elbow_excl_arthritis_codes
):
    actions.create_or_update_codelist(
        owner=organisation,
        name="Changed name",
        slug=codelist.slug,
        new_slug="changed-slug",
        coding_system_id="snomedct",
        coding_system_database_alias=most_recent_database_alias("snomedct"),
        codes=disorder_of_elbow_excl_arthritis_codes,
    )

    codelist.refresh_from_db()

    assert codelist.handles.filter(slug="changed-slug").count() == 1


def test_clone_codelist(new_style_codelist, user, collaborator):
    new_style_codelist.methodology = "Test"
    new_style_version = new_style_codelist.latest_visible_version(collaborator)

    expected_version_count = CodelistVersion.objects.count() + 1
    expected_cached_hierarchy_count = CachedHierarchy.objects.count() + 1
    expected_codeobj_count = (
        CodeObj.objects.count() + new_style_version.code_objs.count()
    )
    expected_search_count = Search.objects.count() + new_style_version.searches.count()
    expected_searchresult_count = SearchResult.objects.count()
    for search in new_style_version.searches.all():
        expected_searchresult_count += search.results.count()

    cloned_codelist = actions.clone_codelist(new_style_codelist, collaborator)

    assert cloned_codelist.owner == collaborator

    # check no references to the source codelist's versions in the clone
    assert (
        set(new_style_codelist.versions.all()).intersection(
            cloned_codelist.versions.all()
        )
        == set()
    )

    # check methodology is retained alongside reference to source
    assert new_style_codelist.methodology in cloned_codelist.methodology
    assert new_style_version.get_absolute_url() in cloned_codelist.methodology

    # check references to References are not the same, but the content is
    assert (
        set(new_style_codelist.references.all()).intersection(
            cloned_codelist.references.all()
        )
        == set()
    )
    assert set(r.text for r in new_style_codelist.references.all()) == set(
        r.text for r in cloned_codelist.references.all()
    )
    assert set(r.url for r in new_style_codelist.references.all()) == set(
        r.url for r in cloned_codelist.references.all()
    )

    # check cloned codelist version
    assert cloned_codelist.versions.count() == 1
    cloned_version = cloned_codelist.versions.first()
    assert cloned_version.status == Status.UNDER_REVIEW
    assert cloned_version.created_at != new_style_version.created_at
    assert cloned_version.updated_at != new_style_version.updated_at

    # check no references to source codelist version's related objects in clone
    # but count is the same
    for field in CodelistVersion._meta.get_fields():
        match field.__class__:
            case reverse_related.OneToOneRel:
                source = getattr(new_style_version, field.name)
                clone = getattr(cloned_version, field.name)
                assert clone is not None
                assert source != clone
            case reverse_related.ManyToOneRel:
                source = set(getattr(new_style_version, field.name).all())
                clone = set(getattr(cloned_version, field.name).all())
                assert source.intersection(clone) == set()
                assert len(source) == len(clone)

    # check searches/code obj multiple relations
    for cloned_search in cloned_version.searches.all():
        original_search = new_style_version.searches.get(slug=cloned_search.slug)
        assert cloned_search.results.count() == original_search.results.count()
        for result in cloned_search.results.all():
            assert result.code_obj in cloned_version.code_objs.all()

    # check we've made the right number of objects
    assert CodelistVersion.objects.count() == expected_version_count
    assert CodeObj.objects.count() == expected_codeobj_count
    assert Search.objects.count() == expected_search_count
    assert SearchResult.objects.count() == expected_searchresult_count
    assert CachedHierarchy.objects.count() == expected_cached_hierarchy_count


def test_clone_codelist_user_own_codelist(user_codelist, organisation_user):
    cloned_codelist = actions.clone_codelist(user_codelist, organisation_user)

    assert user_codelist.name in cloned_codelist.name
    assert "clone" in cloned_codelist.name

    clone2 = actions.clone_codelist(user_codelist, organisation_user)

    assert user_codelist.name in clone2.name
    assert "clone1" in clone2.name


def test_re_clone_organisational_codelist(new_style_codelist, user):
    cloned_codelist = actions.clone_codelist(new_style_codelist, user)

    assert new_style_codelist.name in cloned_codelist.name

    clone2 = actions.clone_codelist(new_style_codelist, user)

    assert new_style_codelist.name in clone2.name
    assert "clone" in clone2.name
