import pytest

from codelists.hierarchy import Hierarchy

from .helpers import MockCodingSystem, build_hierarchy, build_small_hierarchy


def test_nodes():
    hierarchy = build_small_hierarchy()

    assert hierarchy.nodes == {"a", "b", "c", "d", "e", "f"}


def test_parent_map():
    hierarchy = build_small_hierarchy()

    assert len(hierarchy.parent_map) == 5
    for node, children in {
        "b": {"a"},
        "c": {"a"},
        "d": {"b"},
        "e": {"b", "c"},
        "f": {"c"},
    }.items():
        assert hierarchy.parent_map[node] == children


def test_child_map():
    hierarchy = build_small_hierarchy()

    assert len(hierarchy.child_map) == 3
    for node, parents in {
        "a": {"b", "c"},
        "b": {"d", "e"},
        "c": {"e", "f"},
    }.items():
        assert hierarchy.child_map[node] == parents


def test_ancestors():
    hierarchy = build_small_hierarchy()

    for node, ancestors in {
        "a": set(),
        "b": {"a"},
        "c": {"a"},
        "d": {"a", "b"},
        "e": {"a", "b", "c"},
        "f": {"a", "c"},
    }.items():
        assert hierarchy.ancestors(node) == ancestors


def test_descendants():
    hierarchy = build_small_hierarchy()

    for node, descendants in {
        "a": {"b", "c", "d", "e", "f"},
        "b": {"d", "e"},
        "c": {"e", "f"},
        "d": set(),
        "e": set(),
        "f": set(),
    }.items():
        assert hierarchy.descendants(node) == descendants


def test_node_status():
    hierarchy = build_hierarchy()

    def build_node_to_status(included, excluded):
        return {
            node: hierarchy.node_status(node, included, excluded)
            for node in hierarchy.nodes
        }

    assert build_node_to_status(set(), set()) == {
        #        ?
        #       / \
        #      ?   ?
        #     / \ / \
        #    ?   ?   ?
        #   / \ / \ / \
        #  ?   ?   ?   ?
        "a": "?",
        "b": "?",
        "c": "?",
        "d": "?",
        "e": "?",
        "f": "?",
        "g": "?",
        "h": "?",
        "i": "?",
        "j": "?",
    }

    assert build_node_to_status({"a"}, set()) == {
        #        +
        #       / \
        #     (+) (+)
        #     / \ / \
        #   (+) (+) (+)
        #   / \ / \ / \
        # (+) (+) (+) (+)
        "a": "+",
        "b": "(+)",
        "c": "(+)",
        "d": "(+)",
        "e": "(+)",
        "f": "(+)",
        "g": "(+)",
        "h": "(+)",
        "i": "(+)",
        "j": "(+)",
    }

    assert build_node_to_status({"b"}, {"c"}) == {
        #        ?
        #       / \
        #      +   -
        #     / \ / \
        #   (+)  !  (-)
        #   / \ / \ / \
        # (+)  !   !  (-)
        "a": "?",
        "b": "+",
        "c": "-",
        "d": "(+)",
        "e": "!",
        "f": "(-)",
        "g": "(+)",
        "h": "!",
        "i": "!",
        "j": "(-)",
    }

    assert build_node_to_status({"a", "b"}, set()) == {
        #        +
        #       / \
        #      +  (+)
        #     / \ / \
        #   (+) (+) (+)
        #   / \ / \ / \
        # (+) (+) (+) (+)
        "a": "+",
        "b": "+",
        "c": "(+)",
        "d": "(+)",
        "e": "(+)",
        "f": "(+)",
        "g": "(+)",
        "h": "(+)",
        "i": "(+)",
        "j": "(+)",
    }

    assert build_node_to_status({"a"}, {"b"}) == {
        #        +
        #       / \
        #      -  (+)
        #     / \ / \
        #   (-) (-) (+)
        #   / \ / \ / \
        # (-) (-) (-) (+)
        "a": "+",
        "b": "-",
        "c": "(+)",
        "d": "(-)",
        "e": "(-)",
        "f": "(+)",
        "g": "(-)",
        "h": "(-)",
        "i": "(-)",
        "j": "(+)",
    }

    assert build_node_to_status({"a"}, {"b", "c"}) == {
        #        +
        #       / \
        #      -   -
        #     / \ / \
        #   (-) (-) (-)
        #   / \ / \ / \
        # (-) (-) (-) (-)
        "a": "+",
        "b": "-",
        "c": "-",
        "d": "(-)",
        "e": "(-)",
        "f": "(-)",
        "g": "(-)",
        "h": "(-)",
        "i": "(-)",
        "j": "(-)",
    }

    assert build_node_to_status({"a", "e"}, {"b", "c"}) == {
        #        +
        #       / \
        #      -   -
        #     / \ / \
        #   (-)  +  (-)
        #   / \ / \ / \
        # (-) (+) (+) (-)
        "a": "+",
        "b": "-",
        "c": "-",
        "d": "(-)",
        "e": "+",
        "f": "(-)",
        "g": "(-)",
        "h": "(+)",
        "i": "(+)",
        "j": "(-)",
    }


def test_cache_roundtrip():
    hierarchy = build_hierarchy()

    # populate parts of _descendants_cache and _ancestors_cache
    hierarchy.descendants("d")
    hierarchy.ancestors("d")

    hierarchy1 = Hierarchy.from_cache(hierarchy.data_for_cache())

    for name in [
        "root",
        "nodes",
        "child_map",
        "parent_map",
        "_descendants_cache",
        "_ancestors_cache",
    ]:
        assert getattr(hierarchy, name) == getattr(hierarchy1, name)


def test_from_codes_single_code():
    # Make a mock coding system with this structure:
    #        a
    #       / \
    #      b   c
    #     / \ / \
    #    d   e   f
    #   / \ / \ / \
    #  g   h   i   j

    # Using this coding system, the hierarchy built from code f will be:
    #   a
    #   |
    #   c
    #   |
    #   f
    #  / \
    # i   j

    mock_coding_system = MockCodingSystem(build_hierarchy())

    # build a hierarchy for code "f" within the mock coding system
    hierarchy = Hierarchy.from_codes(mock_coding_system, ["f"])
    assert hierarchy.parent_map == {"c": {"a"}, "f": {"c"}, "i": {"f"}, "j": {"f"}}
    assert hierarchy.child_map == {"a": {"c"}, "c": {"f"}, "f": {"i", "j"}}


def test_from_codes_multiple_codes():
    # Make a mock coding system with this structure:
    #        a
    #       / \
    #      b   c
    #     / \ / \
    #    d   e   f
    #   / \ / \ / \
    #  g   h   i   j

    # Using this coding system, the hierarchy built from codes d and f will be:
    #        a
    #       /  \
    #      b    c
    #     /      \
    #    d        f
    #   / \      / \
    #  g   h    i   j

    mock_coding_system = MockCodingSystem(build_hierarchy())

    # build a hierarchy for codes "d" and "f" within the mock coding system
    hierarchy = Hierarchy.from_codes(mock_coding_system, ["d", "f"])
    assert hierarchy.parent_map == {
        "c": {"a"},
        "b": {"a"},
        "d": {"b"},
        "f": {"c"},
        "g": {"d"},
        "h": {"d"},
        "i": {"f"},
        "j": {"f"},
    }
    assert hierarchy.child_map == {
        "a": {"b", "c"},
        "c": {"f"},
        "f": {"i", "j"},
        "b": {"d"},
        "d": {"g", "h"},
    }
    # e is the only code that is not related to either of d or f
    assert "e" not in hierarchy.nodes


def test_from_codes_code_with_no_relationships():
    # Make a mock coding system with this structure:
    #        a
    #       / \
    #      b   c
    #     / \ / \
    #    d   e   f
    #   / \ / \ / \
    #  g   h   i   j

    # A hierarchy can include codes that do not have parents/children (e.g. inactive
    # SNOMED codes)

    # Using this coding system, the hierarchy built from codes f and z will be:

    #     a
    #    / \
    #   c   z
    #   |
    #   f
    #  / \
    # i   j

    mock_coding_system = MockCodingSystem(build_hierarchy())

    # build a hierarchy for code "f" within the mock coding system
    hierarchy = Hierarchy.from_codes(mock_coding_system, ["f", "z"])
    assert hierarchy.parent_map == {
        "c": {"a"},
        "z": {"a"},
        "f": {"c"},
        "i": {"f"},
        "j": {"f"},
    }
    assert hierarchy.child_map == {"a": {"c", "z"}, "c": {"f"}, "f": {"i", "j"}}


def test_from_codes_error():
    mock_coding_system = MockCodingSystem(build_hierarchy())

    # try to pass `codes` as a string
    with pytest.raises(TypeError):
        Hierarchy.from_codes(mock_coding_system, "f")


def test_coding_system_changes_replaced_code():
    """
    Test the impact of changes to coding system on a codelist's hierarchy
    """
    # Release 1:
    #        a
    #       / \
    #      b   c
    #     / \ / \
    #    d   e   f
    #   / \ / \ / \
    #  g   h   i   j

    release_1 = MockCodingSystem(build_hierarchy())

    # In Release 2, d has been replaced with x

    # Release 2:
    #        a
    #       / \
    #      b   c
    #     / \ / \
    #    x   e   f
    #   / \ / \ / \
    #  g   h   i   j

    release2_edges = [
        ("a", "b"),
        ("a", "c"),
        ("b", "x"),
        ("b", "e"),
        ("c", "e"),
        ("c", "f"),
        ("x", "g"),
        ("x", "h"),
        ("e", "h"),
        ("e", "i"),
        ("f", "i"),
        ("f", "j"),
    ]
    release_2 = MockCodingSystem(Hierarchy("a", release2_edges))

    # The coding system changes do not affect the ancestors or descendants of code "f", and
    # the hierarchies built from f for each release is the same
    hierarchy_f_release1 = Hierarchy.from_codes(release_1, ["f"])
    hierarchy_f_release2 = Hierarchy.from_codes(release_2, ["f"])
    assert hierarchy_f_release1.parent_map == hierarchy_f_release2.parent_map
    assert hierarchy_f_release1.child_map == hierarchy_f_release2.child_map

    # However, for b, the hierarchies built for each release are different, because the replaced
    # code d is a descendant of b
    hierarchy_b_release1 = Hierarchy.from_codes(release_1, ["b"])
    hierarchy_b_release2 = Hierarchy.from_codes(release_2, ["b"])
    assert hierarchy_b_release1.parent_map != hierarchy_b_release2.parent_map
    assert hierarchy_b_release1.child_map != hierarchy_b_release2.child_map

    # Similarly, for g, the hierarchies built for each release are different, because the replaced
    # code d is an ancestory of g
    hierarchy_g_release1 = Hierarchy.from_codes(release_1, ["g"])
    hierarchy_g_release2 = Hierarchy.from_codes(release_2, ["g"])
    assert hierarchy_g_release1.parent_map != hierarchy_g_release2.parent_map
    assert hierarchy_g_release1.child_map != hierarchy_g_release2.child_map


def test_coding_system_changes_removed_code():
    """
    Test the impact of changes to coding system on a codelist's hierarchy
    """
    # Release 1:
    #        a
    #       / \
    #      b   c
    #     / \ / \
    #    d   e   f
    #   / \ / \ / \
    #  g   h   i   j

    release_1 = MockCodingSystem(build_hierarchy())

    # In Release 2, e has been removed

    # Release 1:
    #        a
    #       / \
    #      b   c
    #     /     \
    #    d       f
    #   / \     / \
    #  g   h   i   j

    release2_edges = [
        ("a", "b"),
        ("a", "c"),
        ("b", "d"),
        ("c", "f"),
        ("d", "g"),
        ("d", "h"),
        ("f", "i"),
        ("f", "j"),
    ]
    release_2 = MockCodingSystem(Hierarchy("a", release2_edges))

    # The coding system changes do not affect the ancestors or descendants of code "f", and
    # the hierarchies built from f for each release is the same
    hierarchy_f_release1 = Hierarchy.from_codes(release_1, ["f"])
    hierarchy_f_release2 = Hierarchy.from_codes(release_2, ["f"])
    assert hierarchy_f_release1.parent_map == hierarchy_f_release2.parent_map
    assert hierarchy_f_release1.child_map == hierarchy_f_release2.child_map

    # However, for b, the hierarchies built for each release differ, since the removed
    # code e was a child of b
    hierarchy_b_release1 = Hierarchy.from_codes(release_1, ["b"])
    hierarchy_b_release2 = Hierarchy.from_codes(release_2, ["b"])
    assert hierarchy_b_release1.parent_map != hierarchy_b_release2.parent_map
    assert hierarchy_b_release1.child_map != hierarchy_b_release2.child_map


def test_coding_system_changes_new_code():
    """
    Test the impact of changes to coding system on a codelist's hierarchy
    """
    # Release 1:
    #        a
    #       / \
    #      b   c
    #     / \ / \
    #    d   e   f
    #   / \ / \ / \
    #  g   h   i   j

    release_1 = MockCodingSystem(build_hierarchy())

    # In Release 2, a new code has been added

    # Release 2:
    #          a
    #       /  |  \
    #      b   c   aa
    #     / \ / \
    #    d   e   f
    #   / \ / \ / \
    #  g   h   i   j

    release_2_edges = [
        ("a", "b"),
        ("a", "c"),
        ("a", "aa"),
        ("b", "d"),
        ("b", "e"),
        ("c", "e"),
        ("c", "f"),
        ("d", "g"),
        ("d", "h"),
        ("e", "h"),
        ("e", "i"),
        ("f", "i"),
        ("f", "j"),
    ]
    release_2 = MockCodingSystem(Hierarchy("a", release_2_edges))

    # The coding system changes do not affect the immediate ancestors or descendants of code b
    # # the hierarchies built from thesef for each release is the same
    # A new descendant of a has been added up at the top of the hierarchy, but it doesn't
    # directly impact the branches in which b resides
    hierarchy_b_release1 = Hierarchy.from_codes(release_1, ["b"])
    hierarchy_b_release2 = Hierarchy.from_codes(release_2, ["b"])
    assert hierarchy_b_release1.parent_map == hierarchy_b_release2.parent_map
    assert hierarchy_b_release1.child_map == hierarchy_b_release2.child_map

    # In Release 2, another new code has been added, in the middle of the hierarchy

    # Release 2:
    #          a
    #       /  |  \
    #      b   c   aa
    #    / \ / | \
    #   d   e  cc  f
    #  / \ / \   / \
    # g   h    i    j

    release_3_edges = [
        ("a", "b"),
        ("a", "c"),
        ("a", "aa"),
        ("b", "d"),
        ("b", "e"),
        ("c", "e"),
        ("c", "cc"),
        ("c", "f"),
        ("d", "g"),
        ("d", "h"),
        ("e", "h"),
        ("e", "i"),
        ("f", "i"),
        ("f", "j"),
    ]
    release_3 = MockCodingSystem(Hierarchy("a", release_3_edges))

    # code e has parent c, but its hierarchy is not affected by the addition of a
    # new child of c (cc)
    hierarchy_e_release2 = Hierarchy.from_codes(release_2, ["e"])
    hierarchy_e_release3 = Hierarchy.from_codes(release_3, ["e"])
    assert hierarchy_e_release2.parent_map == hierarchy_e_release3.parent_map
    assert hierarchy_e_release2.child_map == hierarchy_e_release3.child_map

    # however, c has a new child, so a hierarchy built from c has changed
    hierarchy_c_release2 = Hierarchy.from_codes(release_2, ["c"])
    hierarchy_c_release3 = Hierarchy.from_codes(release_3, ["c"])
    assert hierarchy_c_release2.parent_map != hierarchy_e_release3.parent_map
    assert hierarchy_c_release2.child_map != hierarchy_c_release3.child_map
