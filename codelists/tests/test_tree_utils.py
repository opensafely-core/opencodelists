from unittest import TestCase

from codelists import tree_utils

from .helpers import build_tree


class TreeUtilsTests(TestCase):
    def test_walk_tree_depth_first(self):
        tree = build_tree(depth=3)

        # tree has this structure:
        #
        #     ┌---1---┐
        #     |       |
        #   ┌-2-┐   ┌-3-┐
        #   |   |   |   |
        #   4   5   6   7

        self.assertEqual(
            list(tree_utils.walk_tree_depth_first(tree)),
            [
                ("1", 1),
                ("2", 1),
                ("4", 1),
                ("4", -1),
                ("5", 1),
                ("5", -1),
                ("2", -1),
                ("3", 1),
                ("6", 1),
                ("6", -1),
                ("7", 1),
                ("7", -1),
                ("3", -1),
                ("1", -1),
            ],
        )
