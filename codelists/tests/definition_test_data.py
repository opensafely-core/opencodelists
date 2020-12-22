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
    },
    {
        "description": "intermediate element only",
        "explicitly_included": "b",
        "explicitly_excluded": "de",
        "codes": "b",
    },
    {
        "description": "leaf element only",
        "explicitly_included": "g",
        "explicitly_excluded": {},
        "codes": "g",
    },
    {
        "description": "root element + descendants",
        "explicitly_included": "a",
        "explicitly_excluded": "",
        "codes": "abcdefghij",
    },
    {
        "description": "root element + all descendants except intermediate",
        "explicitly_included": "ahi",
        "explicitly_excluded": "e",
        "codes": "abcdfghij",
    },
    {
        "description": "root element + all descendants except leaf",
        "explicitly_included": "a",
        "explicitly_excluded": "j",
        "codes": "abcdefghi",
    },
    {
        "description": "intermediate element + descendants",
        "explicitly_included": "b",
        "explicitly_excluded": "",
        "codes": "bdeghi",
    },
    {
        "description": "intermediate element + all descendants except leaf",
        "explicitly_included": "b",
        "explicitly_excluded": "i",
        "codes": "bdegh",
    },
    {
        "description": "root element + descendants of intermediate element",
        "explicitly_included": "ae",
        "explicitly_excluded": "c",
        "codes": "abdeghi",
    },
    {
        "description": "root element - descendants of intermediate element",
        "explicitly_included": "a",
        "explicitly_excluded": "c",
        "codes": "abdg",
    },
]


for example in examples:
    example["explicitly_included"] = set(example["explicitly_included"])
    example["explicitly_excluded"] = set(example["explicitly_excluded"])
    example["codes"] = set(example["codes"])
