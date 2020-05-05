from collections import defaultdict

from django.urls import reverse


def html_tree_highlighting_codes(coding_system, codes):
    subtree = build_subtree(coding_system, codes)
    included_codes = set(tree_depth_first(subtree))
    code_to_name = coding_system.lookup_names(included_codes)

    lines = ["<ul>"]

    last_depth = 0
    for code, depth in tree_depth_first(subtree, code_to_name.__getitem__):
        if depth - last_depth == 1:
            lines.append("<ul>")
        else:
            for i in range(last_depth - depth):
                lines.append("</ul>")

        last_depth = depth

        if code in codes:
            color = "blue"
        else:
            color = "black"

        name = code_to_name[code]
        url = reverse("ctv3:concept", args=[code])

        lines.append(
            f'<li><a href="{url}" style="color: {color}">{name}</a> (<code>{code}</code>)</li>'
        )

    lines.append("</ul>")

    return "\n".join(lines)


def build_subtree(coding_system, codes):
    ancestor_relationships = coding_system.ancestor_relationships(codes)
    descendant_relationships = coding_system.descendant_relationships(codes)
    edges = ancestor_relationships + descendant_relationships
    paths = edges_to_paths(coding_system.root, edges)
    return paths_to_tree(paths)


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


def tree_factory():
    return defaultdict(tree_factory)


def paths_to_tree(paths):
    tree = tree_factory()
    for path in paths:
        subtree = tree
        for node in path:
            subtree = subtree[node]
    return tree


def tree_depth_first(tree, sort_key=None):
    def helper(tree, depth):
        for node in sorted(tree, key=sort_key):
            yield (node, depth)
            yield from (helper(tree[node], depth + 1))

    yield from helper(tree, 0)
