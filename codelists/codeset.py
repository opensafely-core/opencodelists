from .definition import Definition


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

    See examples in definition_test_data.py and test_hierarchy.py (especially
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

        definition = Definition.from_codes(codes, hierarchy)
        codeset = cls.from_definition(
            definition.explicitly_included, definition.explicitly_excluded, hierarchy
        )
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

    def tree(self):
        """Return a tree structure containing the defining codes.

        TODO: rename to `defining_tree`.
        """

        definition = Definition.from_codes(self.codes(), self.hierarchy)
        return definition.tree(self.hierarchy)

    def walk_tree(self, sort_key):
        """Yield tuples of (code, status) found by visiting the defining codes in the
        hierarchy depth first.

        Children are visted in the order of whatever sort_key returns.

        TODO: rename to `walk_defining_tree`.
        """

        definition = Definition.from_codes(self.codes(), self.hierarchy)
        yield from definition.walk_tree(self.hierarchy, sort_key)
