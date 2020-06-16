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
