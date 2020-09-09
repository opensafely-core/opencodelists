from codelists.hierarchy import Hierarchy, NodeWithMetadata


def build_small_hierarchy():
    r"""Return hierarchy with this structure:

        a
       / \
      b   c
     / \ / \
    d   e   f
    """

    edges = [
        ("a", "b"),
        ("a", "c"),
        ("b", "d"),
        ("b", "e"),
        ("c", "e"),
        ("c", "f"),
    ]

    return Hierarchy("a", edges)


def build_hierarchy():
    r"""Return hierarchy with this structure:

           a
          / \
         b   c
        / \ / \
       d   e   f
      / \ / \ / \
     g   h   i   j
    """

    edges = [
        ("a", "b"),
        ("a", "c"),
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

    return Hierarchy("a", edges)


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


def test_walk_depth_first_as_tree_from_root():
    hierarchy = build_small_hierarchy()

    assert list(hierarchy.walk_depth_first_as_tree()) == [
        NodeWithMetadata(label="a", depth=0, left_ix=0, right_ix=0, direction=1),
        NodeWithMetadata(label="b", depth=1, left_ix=0, right_ix=1, direction=1),
        NodeWithMetadata(label="d", depth=2, left_ix=0, right_ix=1, direction=1),
        NodeWithMetadata(label="d", depth=2, left_ix=0, right_ix=1, direction=-1),
        NodeWithMetadata(label="e", depth=2, left_ix=1, right_ix=0, direction=1),
        NodeWithMetadata(label="e", depth=2, left_ix=1, right_ix=0, direction=-1),
        NodeWithMetadata(label="b", depth=1, left_ix=0, right_ix=1, direction=-1),
        NodeWithMetadata(label="c", depth=1, left_ix=1, right_ix=0, direction=1),
        NodeWithMetadata(label="e", depth=2, left_ix=0, right_ix=1, direction=1),
        NodeWithMetadata(label="e", depth=2, left_ix=0, right_ix=1, direction=-1),
        NodeWithMetadata(label="f", depth=2, left_ix=1, right_ix=0, direction=1),
        NodeWithMetadata(label="f", depth=2, left_ix=1, right_ix=0, direction=-1),
        NodeWithMetadata(label="c", depth=1, left_ix=1, right_ix=0, direction=-1),
        NodeWithMetadata(label="a", depth=0, left_ix=0, right_ix=0, direction=-1),
    ]


def test_walk_depth_first_as_tree_from_intermediate_node():
    hierarchy = build_small_hierarchy()

    assert list(hierarchy.walk_depth_first_as_tree(starting_node="b")) == [
        NodeWithMetadata(label="b", depth=0, left_ix=0, right_ix=0, direction=1),
        NodeWithMetadata(label="d", depth=1, left_ix=0, right_ix=1, direction=1),
        NodeWithMetadata(label="d", depth=1, left_ix=0, right_ix=1, direction=-1),
        NodeWithMetadata(label="e", depth=1, left_ix=1, right_ix=0, direction=1),
        NodeWithMetadata(label="e", depth=1, left_ix=1, right_ix=0, direction=-1),
        NodeWithMetadata(label="b", depth=0, left_ix=0, right_ix=0, direction=-1),
    ]


def test_walk_depth_first_as_tree_with_sort_key():
    hierarchy = build_small_hierarchy()

    # The sort_key means that nodes are visited in reverse alphabetical order
    assert list(
        hierarchy.walk_depth_first_as_tree(
            starting_node="b", sort_key=lambda label: -ord(label)
        )
    ) == [
        NodeWithMetadata(label="b", depth=0, left_ix=0, right_ix=0, direction=1),
        NodeWithMetadata(label="e", depth=1, left_ix=0, right_ix=1, direction=1),
        NodeWithMetadata(label="e", depth=1, left_ix=0, right_ix=1, direction=-1),
        NodeWithMetadata(label="d", depth=1, left_ix=1, right_ix=0, direction=1),
        NodeWithMetadata(label="d", depth=1, left_ix=1, right_ix=0, direction=-1),
        NodeWithMetadata(label="b", depth=0, left_ix=0, right_ix=0, direction=-1),
    ]


def test_walk_depth_first_as_tree_with_pipes():
    hierarchy = build_hierarchy()

    # a
    # ├ b
    # │ ├ d
    # │ │ ├ g
    # │ │ └ h
    # │ └ e
    # │   ├ h
    # │   └ i
    # └ c
    #   ├ e
    #   │ ├ h
    #   │ └ i
    #   └ f
    #     ├ i
    #     └ j

    assert list(hierarchy.walk_depth_first_as_tree_with_pipes()) == [
        ("a", []),
        ("b", ["├"]),
        ("d", ["│", "├"]),
        ("g", ["│", "│", "├"]),
        ("h", ["│", "│", "└"]),
        ("e", ["│", "└"]),
        ("h", ["│", " ", "├"]),
        ("i", ["│", " ", "└"]),
        ("c", ["└"]),
        ("e", [" ", "├"]),
        ("h", [" ", "│", "├"]),
        ("i", [" ", "│", "└"]),
        ("f", [" ", "└"]),
        ("i", [" ", " ", "├"]),
        ("j", [" ", " ", "└"]),
    ]


def test_filter_to_ultimate_ancestors():
    hierarchy = build_small_hierarchy()

    #        a
    #       / \
    #      b   c
    #     / \ / \
    #    d   e   f
    assert hierarchy.filter_to_ultimate_ancestors({"a", "b", "c", "d", "e", "f"}) == {
        "a"
    }

    #        .
    #       / \
    #      b   c
    #     / \ / \
    #    d   e   f
    assert hierarchy.filter_to_ultimate_ancestors({"b", "c", "d", "e", "f"}) == {
        "b",
        "c",
    }

    #        a
    #       / \
    #      .   .
    #     / \ / \
    #    d   e   f
    assert hierarchy.filter_to_ultimate_ancestors({"a", "d", "e", "f"}) == {"a"}


def test_update_node_to_status():
    hierarchy = build_hierarchy()

    node_to_status = {
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

    assert hierarchy.update_node_to_status(
        node_to_status, [("a", "-"), ("f", "+"), ("b", "?"), ("a", "+")]
    ) == {
        #        +
        #       / \
        #     (+)  -
        #     / \ / \
        #   (+) (-)  +
        #   / \ / \ / \
        # (+) (-) (+) (+)
        "a": "+",
        "b": "(+)",
        "c": "-",
        "d": "(+)",
        "e": "(-)",
        "f": "+",
        "g": "(+)",
        "h": "(-)",
        "i": "(+)",
        "j": "(+)",
    }


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
