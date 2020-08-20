from codelists import tree_utils

from .helpers import build_tree

# build_tree() returns tree with this structure:
#
#      ┌--a--┐
#      |     |
#   ┌--b--┌--c--┐
#   |     |     |
# ┌-d-┐ ┌-e-┐ ┌-f-┐
# |   | |   | |   |
# g   h i   j k   l


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
        ("i", 1),
        ("i", -1),
        ("j", 1),
        ("j", -1),
        ("e", -1),
        ("b", -1),
        ("c", 1),
        ("e", 1),
        ("i", 1),
        ("i", -1),
        ("j", 1),
        ("j", -1),
        ("e", -1),
        ("f", 1),
        ("k", 1),
        ("k", -1),
        ("l", 1),
        ("l", -1),
        ("f", -1),
        ("c", -1),
        ("a", -1),
    ]
