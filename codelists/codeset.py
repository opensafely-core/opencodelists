class Codeset:
    """A Codeset represents a set of codes within the context of part of a coding system
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

    def all_codes(self):
        """Return all codes in the codeset."""

        return set(self.code_to_status)

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

    def update(self, updates, reset=False):
        """Build new Codeset with given updates applied in turn to self's code_to_status.

        Updates are tuples of (node, new_status), where new_status is one of:

        * +   include this node, and all descendants that are not otherwise excluded
        * -   exclude this node, and all descendants that are not otherwise included
        * ?   clear this node's status, and do so for all descendants that are not otherwise
                included or excluded
        """
        if reset:
            # reset the code_to_status dict so we reapply the directly included and excluded
            # codes again, including any new unknown ones
            self.code_to_status = {code: "?" for code in self.code_to_status}

        directly_included = self.codes("+")
        directly_excluded = self.codes("-")

        assert directly_included & directly_excluded == set()

        for node, status in updates:
            if node in directly_included:
                directly_included.remove(node)
            if node in directly_excluded:
                directly_excluded.remove(node)

            if status == "+":
                directly_included.add(node)
            if status == "-":
                directly_excluded.add(node)

        assert directly_included & directly_excluded == set()

        codes_to_update = set()
        for node, status in updates:
            codes_to_update.add(node)
            codes_to_update |= self.hierarchy.descendants(node)

        code_to_status_updates = {
            code: self.hierarchy.node_status(code, directly_included, directly_excluded)
            for code in codes_to_update
        }

        updated_code_to_status = {**self.code_to_status, **code_to_status_updates}
        return type(self)(updated_code_to_status, self.hierarchy)
