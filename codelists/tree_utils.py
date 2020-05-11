from collections import defaultdict

from django.urls import reverse


def html_tree_highlighting_codes(coding_system, codes):
    subtree = build_subtree(coding_system, codes)
    included_codes = set(walk_tree_depth_first(subtree))
    code_to_name = coding_system.lookup_names(included_codes)
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

        name = code_to_name[code]
        url = reverse("ctv3:concept", args=[code])

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


def walk_tree_depth_first(tree, sort_key=None):
    def helper(tree):
        for node in sorted(tree, key=sort_key):
            yield (node, 1)
            yield from (helper(tree[node]))
            yield (node, -1)

    yield from helper(tree)


def build_descendants_map(tree):
    descendants = {}

    stack = []
    for node, direction in walk_tree_depth_first(tree):
        if direction == 1:
            stack.append(node)
            descendants[node] = set()
        else:
            old_head = stack.pop()
            if stack:
                new_head = stack[-1]
                descendants[new_head].add(old_head)
                descendants[new_head] |= descendants[old_head]

    return descendants
