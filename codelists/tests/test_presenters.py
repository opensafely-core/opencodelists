import re
from pathlib import Path

import pytest
from django.conf import settings
from django.core.management import call_command

from codelists import presenters
from codelists.definition import Definition
from codelists.hierarchy import Hierarchy

from .factories import create_codelist

pytestmark = [
    pytest.mark.filterwarnings(
        "ignore::django.utils.deprecation.RemovedInDjango40Warning:debug_toolbar",
    ),
]


def test_build_html_tree_highlighting_codes():
    fixtures_path = Path(settings.BASE_DIR, "coding_systems", "snomedct", "fixtures")
    call_command("loaddata", fixtures_path / "core-model-components.json")
    call_command("loaddata", fixtures_path / "tennis-elbow.json")

    with open(fixtures_path / "disorder-of-elbow-excl-arthritis.csv") as f:
        cl = create_codelist(csv_data=f.read())

    coding_system = cl.coding_system
    clv = cl.versions.get()
    hierarchy = Hierarchy.from_codes(coding_system, clv.codes)
    definition = Definition.from_codes(set(clv.codes), hierarchy)

    html = presenters.build_html_tree_highlighting_codes(
        coding_system, hierarchy, definition
    )

    with open(
        Path(settings.BASE_DIR, "codelists", "tests", "expected_html_tree.html")
    ) as f:
        assert html.strip() == f.read().strip()


def test_tree_tables():
    fixtures_path = Path(settings.BASE_DIR, "coding_systems", "snomedct", "fixtures")
    call_command("loaddata", fixtures_path / "core-model-components.json")
    call_command("loaddata", fixtures_path / "tennis-elbow.json")

    with open(fixtures_path / "disorder-of-elbow.csv") as f:
        cl = create_codelist(csv_data=f.read())

    clv = cl.versions.get()
    code_to_term_and_type = {
        code: re.match(r"(^.*) \(([\w/ ]+)\)$", term).groups()
        for code, term in cl.coding_system.lookup_names(clv.codes).items()
    }
    code_to_term = {code: term for code, (term, _) in code_to_term_and_type.items()}
    code_to_type = {code: type for code, (_, type) in code_to_term_and_type.items()}
    code_to_status = {code: "?" for code in clv.codes}

    hierarchy = Hierarchy.from_codes(cl.coding_system, clv.codes)
    ancestor_codes = hierarchy.filter_to_ultimate_ancestors(set(clv.codes))

    # 128133004 (Disorder of elbow)
    #   ├  429554009 (Arthropathy of elbow)
    #   │     └  439656005 (Arthritis of elbow)
    #   │           └  202855006 (Lateral epicondylitis)
    #   ├  35185008 (Enthesopathy of elbow region)
    #   │     └  73583000 (Epicondylitis)
    #   │           └  202855006 (Lateral epicondylitis)
    #   └  239964003 (Soft tissue lesion of elbow region)

    assert presenters.tree_tables(
        ancestor_codes, hierarchy, code_to_term, code_to_type, code_to_status
    ) == [
        {
            "heading": "Disorder",
            "rows": [
                {
                    "code": "128133004",
                    "status": "?",
                    "term": "Disorder of elbow",
                    "pipes": [],
                },
                {
                    "code": "429554009",
                    "status": "?",
                    "term": "Arthropathy of elbow",
                    "pipes": ["├"],
                },
                {
                    "code": "439656005",
                    "status": "?",
                    "term": "Arthritis of elbow",
                    "pipes": ["│", "└"],
                },
                {
                    "code": "202855006",
                    "status": "?",
                    "term": "Lateral epicondylitis",
                    "pipes": ["│", " ", "└"],
                },
                {
                    "code": "35185008",
                    "status": "?",
                    "term": "Enthesopathy of elbow region",
                    "pipes": ["├"],
                },
                {
                    "code": "73583000",
                    "status": "?",
                    "term": "Epicondylitis",
                    "pipes": ["│", "└"],
                },
                {
                    "code": "202855006",
                    "status": "?",
                    "term": "Lateral epicondylitis",
                    "pipes": ["│", " ", "└"],
                },
                {
                    "code": "239964003",
                    "status": "?",
                    "term": "Soft tissue lesion of elbow region",
                    "pipes": ["└"],
                },
            ],
        }
    ]
