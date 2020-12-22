# build_hierarchy returns a hierarchy with the following structure:
#
#       a
#      / \
#     b   c
#    / \ / \
#   d   e   f
#  / \ / \ / \
# g   h   i   j


examples = [
    {
        "description": "root element only",
        "explicitly_included": "a",
        "explicitly_excluded": "bc",
        "codes": "a",
        "tree": {("a", "+"): {("b", "-"): {}, ("c", "-"): {}}},
        "tree_rows": [("a", "+"), ("b", "-"), ("c", "-")],
    },
    {
        "description": "intermediate element only",
        "explicitly_included": "b",
        "explicitly_excluded": "de",
        "codes": "b",
        "tree": {("b", "+"): {("d", "-"): {}, ("e", "-"): {}}},
        "tree_rows": [("b", "+"), ("d", "-"), ("e", "-")],
    },
    {
        "description": "leaf element only",
        "explicitly_included": "g",
        "explicitly_excluded": {},
        "codes": "g",
        "tree": {("g", "+"): {}},
        "tree_rows": [("g", "+")],
    },
    {
        "description": "root element + descendants",
        "explicitly_included": "a",
        "explicitly_excluded": "",
        "codes": "abcdefghij",
        "tree": {("a", "+"): {}},
        "tree_rows": [("a", "+")],
    },
    {
        "description": "root element + all descendants except intermediate",
        "explicitly_included": "ahi",
        "explicitly_excluded": "e",
        "codes": "abcdfghij",
        "tree": {("a", "+"): {("e", "-"): {("h", "+"): {}, ("i", "+"): {}}}},
        "tree_rows": [("a", "+"), ("e", "-"), ("h", "+"), ("i", "+")],
    },
    {
        "description": "root element + all descendants except leaf",
        "explicitly_included": "a",
        "explicitly_excluded": "j",
        "codes": "abcdefghi",
        "tree": {("a", "+"): {("j", "-"): {}}},
        "tree_rows": [("a", "+"), ("j", "-")],
    },
    {
        "description": "intermediate element + descendants",
        "explicitly_included": "b",
        "explicitly_excluded": "",
        "codes": "bdeghi",
        "tree": {("b", "+"): {}},
        "tree_rows": [("b", "+")],
    },
    {
        "description": "intermediate element + all descendants except leaf",
        "explicitly_included": "b",
        "explicitly_excluded": "i",
        "codes": "bdegh",
        "tree": {("b", "+"): {("i", "-"): {}}},
        "tree_rows": [("b", "+"), ("i", "-")],
    },
    {
        "description": "root element + descendants of intermediate element",
        "explicitly_included": "ae",
        "explicitly_excluded": "c",
        "codes": "abdeghi",
        "tree": {("a", "+"): {("c", "-"): {("e", "+"): {}}}},
        "tree_rows": [("a", "+"), ("c", "-"), ("e", "+")],
    },
    {
        "description": "root element - descendants of intermediate element",
        "explicitly_included": "a",
        "explicitly_excluded": "c",
        "codes": "abdg",
        "tree": {("a", "+"): {("c", "-"): {}}},
        "tree_rows": [("a", "+"), ("c", "-")],
    },
]


for example in examples:
    example["explicitly_included"] = set(example["explicitly_included"])
    example["explicitly_excluded"] = set(example["explicitly_excluded"])
    example["codes"] = set(example["codes"])
