from codelists import tree_utils

from .helpers import build_tree

# build_tree() returns tree with this structure:
#
#       a
#      / \
#     b   c
#    / \ / \
#   d   e   f
#  / \ / \ / \
# g   h   i   j


def test_walk_tree_depth_first():
    tree = build_tree()

    assert list(tree_utils.walk_tree_depth_first(tree)) == [
        ("a", 1),
        ("b", 1),
        ("d", 1),
        ("g", 1),
        ("g", -1),
        ("h", 1),
        ("h", -1),
        ("d", -1),
        ("e", 1),
        ("h", 1),
        ("h", -1),
        ("i", 1),
        ("i", -1),
        ("e", -1),
        ("b", -1),
        ("c", 1),
        ("e", 1),
        ("h", 1),
        ("h", -1),
        ("i", 1),
        ("i", -1),
        ("e", -1),
        ("f", 1),
        ("i", 1),
        ("i", -1),
        ("j", 1),
        ("j", -1),
        ("f", -1),
        ("c", -1),
        ("a", -1),
    ]


def test_build_relationship_maps():
    tree = build_tree()
    maps = tree_utils.build_relationship_maps(tree)

    ancestors_map = maps["ancestors"]
    assert ancestors_map["a"] == set()
    assert ancestors_map["i"] == {"a", "b", "c", "e", "f"}

    descendants_map = maps["descendants"]
    assert descendants_map["a"] == {
        "b",
        "c",
        "d",
        "e",
        "f",
        "g",
        "h",
        "i",
        "j",
    }
    assert descendants_map["i"] == set()

    for node in "abcdefghi":
        assert node in ancestors_map
        assert node in descendants_map


def test_update():
    tree = build_tree()

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

    assert tree_utils.update(
        tree, node_to_status, [("a", "-"), ("f", "+"), ("b", "?"), ("a", "+")]
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


def test_render():
    tree = build_tree()

    assert tree_utils.render(tree, set(), set()) == {
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

    assert tree_utils.render(tree, {"a"}, set()) == {
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

    assert tree_utils.render(tree, {"b"}, {"c"}) == {
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

    assert tree_utils.render(tree, {"a", "b"}, set()) == {
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

    assert tree_utils.render(tree, {"a"}, {"b"}) == {
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

    assert tree_utils.render(tree, {"a"}, {"b", "c"}) == {
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

    assert tree_utils.render(tree, {"a", "e"}, {"b", "c"}) == {
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


def test_find_ancestors():
    tree = build_tree()

    #       .
    #      / \
    #     b   .
    #    / \ / \
    #   d   e   .
    #  / \ / \ / \
    # .   .   .   .
    assert tree_utils.find_ancestors(tree, {"b", "d", "e"}) == {"b"}

    #       .
    #      / \
    #     b   .
    #    / \ / \
    #   d   e   f
    #  / \ / \ / \
    # .   .   .   .
    assert tree_utils.find_ancestors(tree, {"b", "d", "e", "f"}) == {"b", "f"}

    #       .
    #      / \
    #     b   c
    #    / \ / \
    #   d   e   f
    #  / \ / \ / \
    # .   .   .   .
    assert tree_utils.find_ancestors(tree, {"b", "c", "d", "e", "f"}) == {"b", "c"}

    #       .
    #      / \
    #     .   .
    #    / \ / \
    #   .   e   .
    #  / \ / \ / \
    # g   h   i   j
    assert tree_utils.find_ancestors(tree, {"e", "g", "h", "i", "j"}) == {"e", "g", "j"}
