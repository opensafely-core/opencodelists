"""Tests for tree data building functionality."""

import pytest

from codelists.tree_data import build_tree_data

from .helpers import build_hierarchy


@pytest.fixture(scope="module")
def hierarchy():
    r"""
    Return the simple hierarchy from the helpers file:
           a
          / \
         b   c
        / \ / \
       d   e   f
      / \ / \ / \
     g   h   i   j
    """
    hierarchy = build_hierarchy()
    return hierarchy


@pytest.fixture(scope="module")
def child_map(hierarchy):
    return hierarchy.child_map


@pytest.fixture(scope="module")
def code_to_term(hierarchy):
    return {node: f"{node} - name" for node in hierarchy.nodes}


@pytest.fixture(scope="module")
def code_to_status(hierarchy):
    """Create code_to_status dictionary"""
    # Use the ord function to return the ascii value of the node
    # (which are just lower case characters), then use modulo 2 to
    # ensure we alternate statuses.
    return {node: "+" if ord(node) % 2 == 0 else "-" for node in hierarchy.nodes}


def test_empty_tree():
    """Test building a tree with no nodes"""
    tree_data = build_tree_data({}, {}, {}, [])
    assert tree_data == []


def test_single_node(child_map, code_to_term, code_to_status):
    """Test building a tree with a single node"""
    tree_data = build_tree_data(
        child_map,
        code_to_term,
        code_to_status,
        tree_tables=[("Disorders", ["g"])],
    )
    assert tree_data == [
        {
            "title": "Disorders",
            "children": [
                {
                    "id": "g",
                    "name": code_to_term["g"],
                    "status": code_to_status["g"],
                    "children": [],
                    "depth": 0,
                }
            ],
        }
    ]


def test_basic_tree(child_map, code_to_term, code_to_status):
    """Test building a tree with one parent and 2 children"""
    tree_data = build_tree_data(
        child_map,
        code_to_term,
        code_to_status,
        tree_tables=[("Disorders", ["f"])],
    )
    assert tree_data == [
        {
            "title": "Disorders",
            "children": [
                {
                    "id": "f",
                    "name": code_to_term["f"],
                    "status": code_to_status["f"],
                    "children": [
                        {
                            "id": "i",
                            "name": code_to_term["i"],
                            "status": code_to_status["i"],
                            "children": [],
                            "depth": 1,
                        },
                        {
                            "id": "j",
                            "name": code_to_term["j"],
                            "status": code_to_status["j"],
                            "children": [],
                            "depth": 1,
                        },
                    ],
                    "depth": 0,
                }
            ],
        },
    ]


def test_multiple_trees(child_map, code_to_term, code_to_status):
    """Test with 2 trees. One with children, one without"""
    # Set up tree tables
    tree_tables = [("Tree 1", ["f"]), ("Tree 2", ["g"])]

    # Build the tree data
    tree_data = build_tree_data(child_map, code_to_term, code_to_status, tree_tables)

    assert tree_data == [
        {
            "title": "Tree 1",
            "children": [
                {
                    "id": "f",
                    "name": code_to_term["f"],
                    "status": code_to_status["f"],
                    "children": [
                        {
                            "id": "i",
                            "name": code_to_term["i"],
                            "status": code_to_status["i"],
                            "children": [],
                            "depth": 1,
                        },
                        {
                            "id": "j",
                            "name": code_to_term["j"],
                            "status": code_to_status["j"],
                            "children": [],
                            "depth": 1,
                        },
                    ],
                    "depth": 0,
                }
            ],
        },
        {
            "title": "Tree 2",
            "children": [
                {
                    "id": "g",
                    "name": code_to_term["g"],
                    "status": code_to_status["g"],
                    "children": [],
                    "depth": 0,
                }
            ],
        },
    ]


def test_overlapping_trees(child_map, code_to_term, code_to_status):
    """Test with 2 trees, with some common children"""
    # Set up tree tables
    tree_tables = [("Tree 1", ["d"]), ("Tree 2", ["e"])]

    # Build the tree data
    tree_data = build_tree_data(child_map, code_to_term, code_to_status, tree_tables)

    assert tree_data == [
        {
            "title": "Tree 1",
            "children": [
                {
                    "id": "d",
                    "name": code_to_term["d"],
                    "status": code_to_status["d"],
                    "children": [
                        {
                            "id": "g",
                            "name": code_to_term["g"],
                            "status": code_to_status["g"],
                            "children": [],
                            "depth": 1,
                        },
                        {
                            "id": "h",
                            "name": code_to_term["h"],
                            "status": code_to_status["h"],
                            "children": [],
                            "depth": 1,
                        },
                    ],
                    "depth": 0,
                }
            ],
        },
        {
            "title": "Tree 2",
            "children": [
                {
                    "id": "e",
                    "name": code_to_term["e"],
                    "status": code_to_status["e"],
                    "children": [
                        {
                            "id": "h",
                            "name": code_to_term["h"],
                            "status": code_to_status["h"],
                            "children": [],
                            "depth": 1,
                        },
                        {
                            "id": "i",
                            "name": code_to_term["i"],
                            "status": code_to_status["i"],
                            "children": [],
                            "depth": 1,
                        },
                    ],
                    "depth": 0,
                }
            ],
        },
    ]
