from pathlib import Path

from django.conf import settings
from django.core.management import call_command

from codelists import tree_utils
from codelists.coding_systems import CODING_SYSTEMS

from .helpers import build_small_tree, build_tree


def test_build_subtrees():
    fixtures_path = Path(settings.BASE_DIR, "coding_systems", "snomedct", "fixtures")
    call_command("loaddata", fixtures_path / "core-model-components.json")
    call_command("loaddata", fixtures_path / "tennis-elbow.json")
    coding_system = CODING_SYSTEMS["snomedct"]

    assert tree_utils.build_subtree(coding_system, ["128133004"]) == {
        "138875005": {
            "404684003": {
                "118234003": {
                    "123946008": {
                        "128605003": {
                            "118947000": {
                                "128133004": {
                                    "239964003": {},
                                    "35185008": {"73583000": {"202855006": {}}},
                                    "429554009": {"439656005": {"202855006": {}}},
                                }
                            }
                        }
                    },
                    "301857004": {
                        "302293008": {
                            "116307009": {
                                "116309007": {
                                    "128133004": {
                                        "239964003": {},
                                        "35185008": {"73583000": {"202855006": {}}},
                                        "429554009": {"439656005": {"202855006": {}}},
                                    }
                                },
                                "118947000": {
                                    "128133004": {
                                        "239964003": {},
                                        "35185008": {"73583000": {"202855006": {}}},
                                        "429554009": {"439656005": {"202855006": {}}},
                                    }
                                },
                            },
                            "128605003": {
                                "118947000": {
                                    "128133004": {
                                        "239964003": {},
                                        "35185008": {"73583000": {"202855006": {}}},
                                        "429554009": {"439656005": {"202855006": {}}},
                                    }
                                }
                            },
                        }
                    },
                },
                "64572001": {
                    "123946008": {
                        "128605003": {
                            "118947000": {
                                "128133004": {
                                    "239964003": {},
                                    "35185008": {"73583000": {"202855006": {}}},
                                    "429554009": {"439656005": {"202855006": {}}},
                                }
                            }
                        }
                    }
                },
            }
        }
    }


def test_build_descendant_subtree():
    fixtures_path = Path(settings.BASE_DIR, "coding_systems", "snomedct", "fixtures")
    call_command("loaddata", fixtures_path / "core-model-components.json")
    call_command("loaddata", fixtures_path / "tennis-elbow.json")
    coding_system = CODING_SYSTEMS["snomedct"]

    assert tree_utils.build_descendant_subtree(coding_system, "128133004") == {
        "128133004": {
            "239964003": {},
            "35185008": {"73583000": {"202855006": {}}},
            "429554009": {"439656005": {"202855006": {}}},
        }
    }


# In the following tests, build_small_tree() returns tree with this structure:
#
#       a
#      / \
#     b   c
#    / \ / \
#   d   e   f


def test_walk_tree_depth_first():
    tree = build_small_tree()

    assert list(tree_utils.walk_tree_depth_first(tree)) == [
        ("a", 1),
        ("b", 1),
        ("d", 1),
        ("d", -1),
        ("e", 1),
        ("e", -1),
        ("b", -1),
        ("c", 1),
        ("e", 1),
        ("e", -1),
        ("f", 1),
        ("f", -1),
        ("c", -1),
        ("a", -1),
    ]


def test_walk_tree_depth_first_extra():
    tree = build_small_tree()

    assert list(tree_utils.walk_tree_depth_first_extra(tree)) == [
        ("a", 0, 0, 0, 1),
        ("b", 1, 0, 1, 1),
        ("d", 2, 0, 1, 1),
        ("d", 2, 0, 1, -1),
        ("e", 2, 1, 0, 1),
        ("e", 2, 1, 0, -1),
        ("b", 1, 0, 1, -1),
        ("c", 1, 1, 0, 1),
        ("e", 2, 0, 1, 1),
        ("e", 2, 0, 1, -1),
        ("f", 2, 1, 0, 1),
        ("f", 2, 1, 0, -1),
        ("c", 1, 1, 0, -1),
        ("a", 0, 0, 0, -1),
    ]


# In the following tests, build_tree() returns tree with this structure:
#
#       a
#      / \
#     b   c
#    / \ / \
#   d   e   f
#  / \ / \ / \
# g   h   i   j


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


def test_walk_with_pipes():
    tree = build_tree()

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

    assert list(tree_utils.walk_with_pipes(tree)) == [
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
