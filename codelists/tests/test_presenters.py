import pytest

from codelists import presenters
from codelists.definition import Definition
from codelists.hierarchy import Hierarchy
from coding_systems.snomedct import coding_system as snomed

pytestmark = [
    pytest.mark.filterwarnings(
        "ignore::django.utils.deprecation.RemovedInDjango40Warning:debug_toolbar",
    ),
]


class DummyCodingSystem:
    def lookup_names(self, names):
        return {name: name for name in names}


def test_build_definition_rows():
    # hierarchy has this structure:
    #
    #      ┌--0--┐
    #      |     |
    #   ┌--1--┌--2--┐
    #   |     |     |
    # ┌-3-┐ ┌-4-┐ ┌-5-┐
    # |   | |   | |   |
    # 6   7 8   9 10 11

    edges = [
        ("0", "1"),
        ("0", "2"),
        ("1", "3"),
        ("1", "4"),
        ("2", "4"),
        ("2", "5"),
        ("3", "6"),
        ("3", "7"),
        ("4", "8"),
        ("4", "9"),
        ("5", "10"),
        ("5", "11"),
    ]
    hierarchy = Hierarchy("0", edges)

    # construct a hierarchy with 2, and all its descendants except 8
    definition = Definition.from_codes({"2", "4", "5", "9", "10", "11"}, hierarchy)

    # make a dummy coding system so we can do name lookup
    dummy_coding_system = DummyCodingSystem()

    rows = presenters.build_definition_rows(dummy_coding_system, hierarchy, definition)

    # we expect only one row (with an exclusion for 8)
    assert len(rows) == 1

    row = rows[0]
    assert row["code"] == "2"
    assert row["all_descendants"]

    # the only excluded code should be 8
    assert len(row["excluded_descendants"]) == 1
    excluded = row["excluded_descendants"][0]
    assert excluded["code"] == "8"


def test_tree_tables(tennis_elbow_codelist):
    cl = tennis_elbow_codelist
    clv = cl.versions.get()

    hierarchy = Hierarchy.from_codes(cl.coding_system, clv.codes)
    ancestor_codes = hierarchy.filter_to_ultimate_ancestors(set(clv.codes))
    codes_by_type = snomed.codes_by_type(ancestor_codes, hierarchy)
    code_to_term = snomed.code_to_term(hierarchy.nodes)

    # 128133004 (Disorder of elbow)
    #   ├  429554009 (Arthropathy of elbow)
    #   │     └  439656005 (Arthritis of elbow)
    #   │           └  202855006 (Lateral epicondylitis)
    #   ├  35185008 (Enthesopathy of elbow region)
    #   │     └  73583000 (Epicondylitis)
    #   │           └  202855006 (Lateral epicondylitis)
    #   └  239964003 (Soft tissue lesion of elbow region)

    assert presenters.tree_tables(codes_by_type, hierarchy, code_to_term) == [
        {
            "heading": "Disorder",
            "rows": [
                {
                    "code": "128133004",
                    "term": "Disorder of elbow",
                    "pipes": [],
                },
                {
                    "code": "429554009",
                    "term": "Arthropathy of elbow",
                    "pipes": ["├"],
                },
                {
                    "code": "439656005",
                    "term": "Arthritis of elbow",
                    "pipes": ["│", "└"],
                },
                {
                    "code": "202855006",
                    "term": "Lateral epicondylitis",
                    "pipes": ["│", " ", "└"],
                },
                {
                    "code": "35185008",
                    "term": "Enthesopathy of elbow region",
                    "pipes": ["├"],
                },
                {
                    "code": "73583000",
                    "term": "Epicondylitis",
                    "pipes": ["│", "└"],
                },
                {
                    "code": "202855006",
                    "term": "Lateral epicondylitis",
                    "pipes": ["│", " ", "└"],
                },
                {
                    "code": "239964003",
                    "term": "Soft tissue lesion of elbow region",
                    "pipes": ["└"],
                },
            ],
        }
    ]
