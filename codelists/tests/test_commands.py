from io import StringIO

from django.core.management import call_command


def output_from_call_command(command, *args):
    out = StringIO()
    err = StringIO()
    call_command(
        command,
        *args,
        stdout=out,
        stderr=err,
    )
    return out.getvalue().strip(), err.getvalue().strip()


def test_update_draft_no_matching_version():
    out, err = output_from_call_command("update_draft", "foo")
    assert out == ""
    assert err == "No CodelistVersion found with hash 'foo'"


def test_update_draft_version_not_draft(version_with_some_searches):
    assert version_with_some_searches.status == "under review"
    out, err = output_from_call_command("update_draft", version_with_some_searches.hash)
    assert out == ""
    assert (
        err
        == f"CodelistVersion '{version_with_some_searches.hash}' is not a draft (under review)"
    )


def test_update_draft_version_no_changes_needed(draft_with_some_searches):
    out, err = output_from_call_command("update_draft", draft_with_some_searches.hash)
    assert (
        out == f"CodelistVersion {draft_with_some_searches.hash}: no changes required"
    )
    assert err == ""


def test_update_draft_version_with_changes(draft_with_complete_searches):
    # Test that a draft that requires an update outputs the expected messages
    # Note the updates themselves are tested in codelists/test_actions.py::test_update_draft_codeset

    # delete a CodeObj that's included by a parent from the draft to simulate a new concept on the
    # coding system
    missing_implicit_concept = draft_with_complete_searches.code_objs.filter(
        status="(+)"
    ).first()
    missing_code = missing_implicit_concept.code
    missing_implicit_concept.delete()

    out, err = output_from_call_command(
        "update_draft", draft_with_complete_searches.hash
    )
    assert (
        out
        == f"CodelistVersion {draft_with_complete_searches.hash} updated:\n{missing_code} - (+) (new)"
    )
    assert err == ""
