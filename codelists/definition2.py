class Definition2:
    r"""A Definition2 is a compact way to define a list of codes.

    It consists of a set of codes that are included with their descendants, and a set of
    codes that are excluded with their descendants.  This matches the structure used to
    build a codelist with the builder.

    For instance, given a hierarchy with the following structure:

          a
         / \
        b   c
       / \ / \
      d   e   f
     / \ / \ / \
    g   h   i   j

    then ["a", "b", "d", "e", "g", "h", "i"] can be defined by including "a" and "e"
    (and descendants), and excluding "c" (and descendants).

    This is different to the existing Definition class, which does not allow for
    excluding a concept and all of its descendents.  We need this, in order to be able
    to allow codelists to be edited in the builder.

    The existing Definition class may go away, in which case we'll rename this to
    Definition.
    """

    def __init__(self, included_ancestors, excluded_ancestors):
        self.included_ancestors = included_ancestors
        self.excluded_ancestors = excluded_ancestors

    @classmethod
    def from_codes(cls, codes, hierarchy):
        """Build a Definition2 from a set of codes."""

        included_ancestors = set()
        excluded_ancestors = set()

        def including_helper(included_codes):
            """Add ancestors of included_codes to included_ancestors, and pass off
            handling excluded descendants of these ancestors to excluding_helper.
            """

            for ancestor in hierarchy.filter_to_ultimate_ancestors(included_codes):
                included_ancestors.add(ancestor)
                descendants = hierarchy.descendants(ancestor)

                if not descendants < included_codes:
                    # Some of this ancestor's descendants are to be excluded (with their
                    # descendants).
                    excluding_helper(descendants - included_codes)

        def excluding_helper(excluded_codes):
            """Add ancestors of excluded_codes to excluded_ancestors, and pass off
            handling included descendants of these ancestors to including_helper.
            """

            for ancestor in hierarchy.filter_to_ultimate_ancestors(excluded_codes):
                excluded_ancestors.add(ancestor)
                descendants = hierarchy.descendants(ancestor)

                if not descendants < excluded_codes:
                    # Some of this ancestor's descendants are to be included (with their
                    # descendants).
                    including_helper(descendants - excluded_codes)

        including_helper(codes)

        return cls(included_ancestors, excluded_ancestors)

    def codes(self, hierarchy):
        """Return the codes defined by this Definition2."""

        return {
            node
            for node in hierarchy.nodes
            if hierarchy.node_status(
                node, self.included_ancestors, self.excluded_ancestors
            )
            in ["+", "(+)"]
        }

    def all_related_codes(self, hierarchy):
        """Return all codes related to this definition."""

        all_codes = set()
        included_codes = self.codes(hierarchy)

        for ancestor_code in hierarchy.filter_to_ultimate_ancestors(included_codes):
            all_codes.add(ancestor_code)
            all_codes |= hierarchy.descendants(ancestor_code)

        return all_codes

    def code_to_status(self, hierarchy):
        """Return mapping from code to status for all codes defined by this definition,
        and their descendants.
        """

        return {
            code: hierarchy.node_status(
                code, self.included_ancestors, self.excluded_ancestors
            )
            for code in self.all_related_codes(hierarchy)
        }
