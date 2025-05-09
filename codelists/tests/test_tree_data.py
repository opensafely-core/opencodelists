"""Tests for tree data building functionality."""

from codelists.hierarchy import Hierarchy
from codelists.tree_data import build_tree_data

from .helpers import MockCodingSystem


def test_build_tree_data():
    """Test that tree data is correctly built from a hierarchy."""
    # Create a simple hierarchy
    hierarchy = {
        "A": ["A1", "A2"],
        "A1": ["A1a"],
        "A2": [],
        "A1a": [],
    }

    # Create a mock coding system with the hierarchy
    coding_system = MockCodingSystem()
    coding_system.hierarchy = Hierarchy.from_dict(hierarchy)

    # Set up code to term mapping
    code_to_term = {
        "A": "Root",
        "A1": "Child 1",
        "A2": "Child 2",
        "A1a": "Grandchild",
    }

    # Set up code to status mapping
    code_to_status = {
        "A": "+",
        "A1": "+",
        "A2": "-",
        "A1a": "+",
    }

    # Set up tree tables
    tree_tables = [("Test Tree", ["A"])]

    # Build the tree data
    tree_data = build_tree_data(
        coding_system.hierarchy.child_map, code_to_term, code_to_status, tree_tables
    )

    # Verify the structure
    assert len(tree_data) == 1
    assert tree_data[0]["title"] == "Test Tree"

    # Check root node
    root = tree_data[0]["children"][0]
    assert root["id"] == "A"
    assert root["name"] == "Root"
    assert root["status"] == "+"
    assert root["depth"] == 0
    assert len(root["children"]) == 2

    # Check first level children
    children = sorted(root["children"], key=lambda x: x["name"])
    assert children[0]["id"] == "A1"
    assert children[0]["name"] == "Child 1"
    assert children[0]["status"] == "+"
    assert children[0]["depth"] == 1

    assert children[1]["id"] == "A2"
    assert children[1]["name"] == "Child 2"
    assert children[1]["status"] == "-"
    assert children[1]["depth"] == 1

    # Check grandchild
    grandchild = children[0]["children"][0]
    assert grandchild["id"] == "A1a"
    assert grandchild["name"] == "Grandchild"
    assert grandchild["status"] == "+"
    assert grandchild["depth"] == 2
    assert len(grandchild["children"]) == 0
