from collections import defaultdict

from django.urls import reverse


def build_html_tree_highlighting_codes(coding_system, subtree, definition):
    codes = definition.codes(subtree)
    codes_in_definition = {e.code for e in definition.unnegated_elements()}
    codes_in_tree = set(walk_tree_depth_first(subtree))
    code_to_name = coding_system.lookup_names(codes_in_tree)
    sort_key = code_to_name.__getitem__

    lines = []
    last_direction = 1
    for code, direction in walk_tree_depth_first(subtree, sort_key):
        if direction == last_direction == 1:
            lines.append("<ul>")
        elif direction == last_direction == -1:
            lines.append("</ul>")

        last_direction = direction

        if direction == -1:
            continue

        if code in codes:
            colour = "blue"
        else:
            colour = "black"

        style = f"color: {colour}"

        if code in codes_in_definition:
            style += "; text-decoration: underline"

        name = code_to_name[code]
        url = reverse(f"{coding_system.id}:concept", args=[code])

        lines.append(
            f'<li><a href="{url}" style="{style}">{name}</a> (<code>{code}</code>)</li>'
        )

    return "\n".join(lines)


def build_subtree(coding_system, codes):
    ancestor_relationships = coding_system.ancestor_relationships(codes)
    descendant_relationships = coding_system.descendant_relationships(codes)
    edges = ancestor_relationships + descendant_relationships
    paths = edges_to_paths(coding_system.root, edges)
    return paths_to_tree(paths)


def build_descendant_subtrees(coding_system, codes):
    descendant_relationships = coding_system.descendant_relationships(codes)
    return [
        paths_to_tree(edges_to_paths(code, descendant_relationships)) for code in codes
    ]


def edges_to_paths(root, edges):
    map = defaultdict(set)

    for parent, child in edges:
        map[parent].add(child)

    paths = []
    todo = [[root]]

    while todo:
        path = todo.pop()
        next_nodes = map[path[-1]]
        if not next_nodes:
            paths.append(path)
        else:
            for next_node in next_nodes:
                todo.append(path + [next_node])

    return paths


def paths_to_tree(paths):
    tree = {}
    for path in paths:
        subtree = tree
        for node in path:
            if node not in subtree:
                subtree[node] = {}
            subtree = subtree[node]
    return tree


def walk_tree_depth_first(tree, sort_key=None):
    def helper(tree):
        for node in sorted(tree, key=sort_key):
            yield (node, 1)
            yield from (helper(tree[node]))
            yield (node, -1)

    yield from helper(tree)


def build_relationship_maps(tree):
    """Return dict that maps "ancestors" and "descendants" to dicts that map
    each node to the set of nodes that are ancestors or descendants of that
    node.

    Eg for this tree:

       ┌--a--┐
       |     |
       b     c

    It returns:

    {
        "ancestors": {"a": {"b", "c"}, "b": set(), "c": set()},
        "descendants": {"a": set(), "b": {"a"}, "c": {"a"},
    }
    """

    descendants_map = {}
    ancestors_map = {}

    stack = []
    for node, direction in walk_tree_depth_first(tree):
        if node not in ancestors_map:
            ancestors_map[node] = set()
        if node not in descendants_map:
            descendants_map[node] = set()

        if direction == 1:
            # We're moving away from the root, from parent to child.
            child = node
            if stack:
                parent = stack[-1]
                ancestors_map[child].add(parent)
                ancestors_map[child] |= ancestors_map[parent]
            stack.append(node)
        else:
            # We're moving towards the root, from child to parent.
            child = stack.pop()
            if stack:
                parent = stack[-1]
                descendants_map[parent].add(child)
                descendants_map[parent] |= descendants_map[child]

    return {"descendants": descendants_map, "ancestors": ancestors_map}


def build_descendants_map(tree):
    """Return "descendants" dict from build_relationship_maps."""
    return build_relationship_maps(tree)["descendants"]


def build_ancestors_map(tree):
    """Return "ancestors" dict from build_relationship_maps."""
    return build_relationship_maps(tree)["ancestors"]


def render(tree, included, excluded):
    r"""Return a mapping from each node in the tree to that node's status, which
    can be one of:

    * +   included directly
    * -   excluded directly
    * (+) included indirectly by one or more ancestors
    * (-) excluded indirectly by one or more ancestors
    * ?   neither included nor excluded
    * !   in conflict: has some ancestors which are directly included and some
            which are directly excluded, and neither set overrides the other

    For example, for this tree:

           a
          / \
         b   c
        / \ / \
       d   e   f
      / \ / \ / \
     g   h   i   j

    with a and e included, and b and c excluded, nodes will have the statues according
    to this diagram:

           +
          / \
         -   -
        / \ / \
      (-)  +  (-)
      / \ / \ / \
    (-) (+) (+) (-)

    So render(tree, {"a", "e"}, {"b", "c"}) returns

    {
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

    See test_render for more examples.
    """

    assert included & excluded == set()
    relationship_maps = build_relationship_maps(tree)
    ancestors_map = relationship_maps["ancestors"]
    descendants_map = relationship_maps["descendants"]

    def render_node(node):
        if node in included:
            # this node is explicitly included
            return "+"
        if node in excluded:
            # this node is explicitly excluded
            return "-"

        # these are the ancestors of the node
        ancestors = ancestors_map[node]

        # these are the ancestors of the node that are directly included or excluded
        included_or_excluded_ancestors = ancestors & (included | excluded)

        # these are the ancestors of the node that are directly included or excluded,
        # and which are not overridden by any of their descendants
        significant_included_or_excluded_ancestors = {
            a
            for a in included_or_excluded_ancestors
            if not (included_or_excluded_ancestors & descendants_map[a])
        }

        # these are the significant included ancestors of the node
        included_ancestors = significant_included_or_excluded_ancestors & included

        # these are the significant excluded ancestors of the node
        excluded_ancestors = significant_included_or_excluded_ancestors & excluded

        if not included_ancestors and not excluded_ancestors:
            # no ancestors are included or excluded, so this node is neither excluded or
            # excluded
            return "?"
        if included_ancestors and not excluded_ancestors:
            # some ancestors are included and none are excluded, so this node is
            # included
            return "(+)"
        if excluded_ancestors and not included_ancestors:
            # some ancestors are excluded and none are included, so this node is
            # excluded
            return "(-)"

        # some ancestors are included and some are excluded, and neither set of
        # ancestors overrides the other
        return "!"

    return {node: render_node(node) for node in ancestors_map}
