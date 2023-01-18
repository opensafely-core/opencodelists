import csv
from io import StringIO

from django.core.management import call_command

from codelists.models import CodeObj, Handle


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


def test_update_draft_output(draft_with_complete_searches):
    # Test that a draft that requires an update outputs the expected message

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


def test_update_draft_codeset_new_code(minimal_draft):
    """
    There are 4 codes on minimal_draft:
    2 directly included and 2 implicitly included, as the result of searches for
    "tennis toe" and "Enthesopathy of elbow"
    Note 202855006 is a descendant of both 3723001/439656005 (not included) and 35185008/73583000 (included)

    ..  3723001         Arthritis
    ..  439656005       └ Arthritis of elbow
    (+) 202855006         └ Lateral epicondylitis
    ..  116309007       Finding of elbow region
    ..  128133004       ├ Disorder of elbow
    ..  429554009       │ ├ Arthropathy of elbow
    ..  439656005       │ │ └ Arthritis of elbow
    ..  202855006       │ │   └ Lateral epicondylitis
    +   35185008        │ ├ Enthesopathy of elbow region
    (+) 73583000        │ │ └ Epicondylitis
    (+) 202855006       │ │   └ Lateral epicondylitis
    ..  239964003       │ └ Soft tissue lesion of elbow region
    ..  298869002       └ Finding of elbow joint
    ..  429554009         ├ Arthropathy of elbow
    ..  439656005         │ └ Arthritis of elbow
    ..  202855006         │   └ Lateral epicondylitis
    ..  298163003         └ Elbow joint infla
    ..  439656005           └ Arthritis of elbow
    ..  202855006             └ Lateral epicondylitis
    ..  238484001       Tennis toe
    +   156659008       (Epicondylitis &/or tennis elbow) or (golfers' elbow) [inactive]
    """

    # Searches for "tennis toe" and "Enthesopathy of elbow" will return these 4 codes
    initial_code_to_status = {
        "238484001": "+",
        "73583000": "(+)",
        "202855006": "(+)",
        "35185008": "+",
    }
    assert minimal_draft.codeset.code_to_status == initial_code_to_status

    # Set up the test scenarios
    # Manipulate the code objs to represent a previous state of the coding system

    # 1) 202855006 is a new code that will be returned when the searches are re-run
    # i.e. in previous version
    # +   73583000        │ ├ Epicondylitis
    # (+) 35185008        │ │ └ Enthesopathy of elbow region
    # in new version
    # +   35185008        │ ├ Enthesopathy of elbow region
    # (+) 73583000        │ │ └ Epicondylitis
    # (+) 202855006       │ │   └ Lateral epicondylitis

    # SET UP: Delete 202855006 from the version
    CodeObj.objects.get(version=minimal_draft, code="202855006").delete()
    # This is the state of the codeset's code_to_status based on searches
    # that did NOT return 202855006
    assert minimal_draft.codeset.code_to_status == {
        "238484001": "+",
        "73583000": "(+)",
        "35185008": "+",
    }

    # update the draft to recreate its searches and derived statuses
    call_command("update_draft", minimal_draft.hash)

    # the "new" code has been set to its expected inherited status
    assert minimal_draft.codeset.code_to_status == initial_code_to_status


def test_update_draft_codeset_swapped_codes(minimal_draft):
    # Searches for "tennis toe" and "Enthesopathy of elbow" will return these 4 codes
    initial_code_to_status = {
        "238484001": "+",
        "73583000": "(+)",
        "202855006": "(+)",
        "35185008": "+",
    }
    assert minimal_draft.codeset.code_to_status == initial_code_to_status

    # Set up the test scenarios
    # Manipulate the code objs to represent a previous state of the coding system

    # Assume that 73583000 (Epicondylitis) and 35185008 (Enthesopathy of elbow region)
    # have swapped places - ie. 73583000 used to be the parent of 35185008 and 202855006,
    # and was explicitly included, with 35185008 implicitly included

    # i.e. in previous version
    # +   73583000        │ ├ Epicondylitis
    # (+) 35185008        │ │ └ Enthesopathy of elbow region
    # (+) 202855006       │ │   └ Lateral epicondylitis
    # in new version 73583000 is still included, and 202855006 is implicitly included by it
    # but the new parent 35185008 is now unresolved
    # ?   35185008        │ ├ Enthesopathy of elbow region
    # +   73583000        │ │ └ Epicondylitis
    # (+) 202855006       │ │   └ Lateral epicondylitis

    # SET UP: Update the status of the two codes
    code_35185008 = CodeObj.objects.get(version=minimal_draft, code="35185008")
    code_35185008.status = "(+)"
    code_35185008.save()
    code_73583000 = CodeObj.objects.get(version=minimal_draft, code="73583000")
    code_73583000.status = "+"
    code_73583000.save()
    assert minimal_draft.codeset.code_to_status == {
        "238484001": "+",
        "73583000": "+",
        "202855006": "(+)",
        "35185008": "(+)",
    }
    # update the draft to recreate its searches and derived statuses
    call_command("update_draft", minimal_draft.hash)
    # 35185008 was implicitly included by inclusion of 73583000, but now it is the
    # parent of 73583000.  Its status has been updated to '?'; this is OK for the
    # frontend, because it has no ancestors that are included/excluded
    # 202855006 is still a child of the explicity included 73583000, so it remains
    # implicitly included
    assert minimal_draft.codeset.code_to_status == {
        "35185008": "?",
        "73583000": "+",
        "238484001": "+",
        "202855006": "(+)",
    }


def test_update_draft_codeset_replaced_code(minimal_draft):
    # Searches for "tennis toe" and "Enthesopathy of elbow" will return these 4 codes
    initial_code_to_status = {
        "238484001": "+",
        "73583000": "(+)",
        "202855006": "(+)",
        "35185008": "+",
    }
    assert minimal_draft.codeset.code_to_status == initial_code_to_status

    # Set up the test scenarios
    # Manipulate the code objs to represent a previous state of the coding system

    # Assume that the hierarchy has changed so 73583000 is a replacement for another
    # code 99999999 which no longer exists

    # i.e. in previous version
    # +   35185008        │ ├ Enthesopathy of elbow region
    # (+) 99999999        │ │ └ Epicondylitis
    # (+) 202855006       │ │   └ Lateral epicondylitis
    # in new version
    # +   35185008        │ ├ Enthesopathy of elbow region
    # (+) 73583000        │ │ └ Epicondylitis
    # (+) 202855006       │ │   └ Lateral epicondylitis

    # SETUP: delete 73583000 and create 99999999
    CodeObj.objects.get(version=minimal_draft, code="73583000").delete()
    CodeObj.objects.create(version=minimal_draft, code="99999999", status="(+)")
    assert minimal_draft.codeset.code_to_status == {
        "35185008": "+",
        "99999999": "(+)",
        "238484001": "+",
        "202855006": "(+)",
    }
    # update the draft to recreate its searches and derived statuses
    call_command("update_draft", minimal_draft.hash)
    # 99999999 has been replaced by 73583000, and is now implicitly included by inclusion
    # of its parent 35185008

    assert minimal_draft.codeset.code_to_status == initial_code_to_status


def test_convert_bnf_versions_to_dmd(
    bnf_version_asthma, bnf_version_with_search, tmp_path
):
    # setup csv input data with URLs for the two bnf versions, and two bad urls
    with open(tmp_path / "bnf_versions_to_convert.csv", "w") as data_f:
        writer = csv.writer(data_f)
        writer.writerows(
            [
                ["URL"],
                [bnf_version_asthma.get_absolute_url()],
                [bnf_version_with_search.get_absolute_url()],
                ["http://bad-codelist/version/123"],
                ["http://bad-codelist/version/"],
            ]
        )

    call_command(
        "convert_bnf_versions_to_dmd", tmp_path / "bnf_versions_to_convert.csv"
    )
    converted_dmd_codelist = Handle.objects.get(
        slug=f"{bnf_version_asthma.codelist.slug}-dmd"
    ).codelist

    report_path = tmp_path / "bnf_versions_to_convert_converted.csv"
    assert report_path.exists()
    with open(report_path) as report_f:
        reader = csv.DictReader(report_f)
        rows = list(reader)

    assert rows == [
        # versions are converted in the order they are found in the input CSV
        # bnf_version_asthma is converted to the new dmd codelist
        {
            "BNF version": bnf_version_asthma.get_absolute_url(),
            "dm+d codelist": converted_dmd_codelist.get_absolute_url(),
            "created": "True",
            "comments": "",
        },
        # bnf_version_with_search is a version of the same bnf codelist, so it is not converted again
        {
            "BNF version": bnf_version_with_search.get_absolute_url(),
            "dm+d codelist": converted_dmd_codelist.get_absolute_url(),
            "created": "False",
            "comments": "already exists",
        },
        # the bad URLs are reported as not found, with relevant line number
        {
            "BNF version": "http://bad-codelist/version/123",
            "dm+d codelist": "",
            "created": "False",
            "comments": "BNF version not found (input file row 3)",
        },
        # the bad URLs are reported as not found, with its relevant line number
        {
            "BNF version": "http://bad-codelist/version/",
            "dm+d codelist": "",
            "created": "False",
            "comments": "BNF version not found (input file row 4)",
        },
    ]
