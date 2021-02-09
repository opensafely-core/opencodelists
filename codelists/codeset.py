class Codeset:
    r"""A Codeset represents a set of codes within the context of part of a coding system
    hierarchy.

    Each code in a Codeset has a status, which is one of the following:

        * +   included directly
        * -   excluded directly
        * (+) included indirectly by one or more ancestors
        * (-) excluded indirectly by one or more ancestors
        * ?   neither included nor excluded
        * !   in conflict: has some ancestors which are directly included and some which are
                directly excluded, and neither set overrides the other

    Codes which are directly included or excluded are called defining codes.  The status
    of all other codes can be determined from the defining codes.  The defining codes
    are together called the definition.

    See examples in codeset_test_data.py and test_hierarchy.py (especially
    test_node_status) for examples.

    Note to reviewers: for now, this is a wrapper around functionality in Definition
    (which will go away) and Hierarchy (which will lose some methods).
    """

    def __init__(self, code_to_status, hierarchy):
        """Initalise a Codeset with a mapping from code to status, and a hierarchy.

        See class docstring for possible status values.
        """

        self.code_to_status = code_to_status
        self.hierarchy = hierarchy

    @classmethod
    def from_definition(cls, directly_included, directly_excluded, hierarchy):
        """Build Codeset from definition and hierarchy."""

        directly_included_or_excluded = directly_included | directly_excluded
        code_to_status = {
            code: hierarchy.node_status(code, directly_included, directly_excluded)
            for code in hierarchy.nodes
            if code in directly_included_or_excluded
            or hierarchy.ancestors(code) & directly_included_or_excluded
        }
        return cls(code_to_status, hierarchy)

    @classmethod
    def from_codes(cls, codes, hierarchy):
        """Build Codeset from set of codes and hierarchy."""

        directly_included = set()
        directly_excluded = set()

        def including_helper(included_codes):
            """Add ancestors of included_codes to directly_included, and pass off
            handling excluded descendants of these ancestors to excluding_helper.
            """

            for ancestor in hierarchy.filter_to_ultimate_ancestors(included_codes):
                directly_included.add(ancestor)
                descendants = hierarchy.descendants(ancestor)

                if not descendants < included_codes:
                    # Some of this ancestor's descendants are to be excluded (with their
                    # descendants).
                    excluding_helper(descendants - included_codes)

        def excluding_helper(excluded_codes):
            """Add ancestors of excluded_codes to directly_excluded, and pass off
            handling included descendants of these ancestors to including_helper.
            """

            for ancestor in hierarchy.filter_to_ultimate_ancestors(excluded_codes):
                directly_excluded.add(ancestor)
                descendants = hierarchy.descendants(ancestor)

                if not descendants < excluded_codes:
                    # Some of this ancestor's descendants are to be included (with their
                    # descendants).
                    including_helper(descendants - excluded_codes)

        including_helper(codes)

        codeset = cls.from_definition(directly_included, directly_excluded, hierarchy)
        assert sorted(codeset.codes()) == sorted(codes)
        return codeset

    def codes(self, statuses=None):
        """Return set of codes with given status(es).

        If no statuses are provided, return codes that are included.
        """

        if statuses is None:
            statuses = ["+", "(+)"]
        if isinstance(statuses, str):
            statuses = [statuses]

        return {
            code for code, status in self.code_to_status.items() if status in statuses
        }

    def defining_tree(self):
        """Return a tree structure containing the defining codes."""

        def including_helper(directly_included, directly_excluded):
            tree = {}
            for ancestor in self.hierarchy.filter_to_ultimate_ancestors(
                directly_included
            ):
                descendants = self.hierarchy.descendants(ancestor)
                tree[(ancestor, "+")] = excluding_helper(
                    descendants & directly_included, descendants & directly_excluded
                )
            return tree

        def excluding_helper(directly_included, directly_excluded):
            tree = {}
            for ancestor in self.hierarchy.filter_to_ultimate_ancestors(
                directly_excluded
            ):
                descendants = self.hierarchy.descendants(ancestor)
                tree[(ancestor, "-")] = including_helper(
                    descendants & directly_included, descendants & directly_excluded
                )
            return tree

        return including_helper(self.codes("+"), self.codes("-"))

    def walk_defining_tree(self, sort_key):
        """Yield tuples of (code, status) found by visiting the defining codes in the
        hierarchy depth first.

        Children are visted in the order of whatever sort_key returns.
        """

        def helper(tree):
            if not tree:
                return

            codes = sorted((code for (code, _) in tree), key=sort_key)
            _, status = list(tree)[0]

            for code in codes:
                yield (code, status)
                yield from helper(tree[(code, status)])

        yield from helper(self.defining_tree())
