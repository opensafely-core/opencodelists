from collections import defaultdict


def tree_factory():
    return defaultdict(tree_factory)


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


def prune_paths(paths, nodes):
    return [path for path in paths if any(node in path for node in nodes)]


def paths_to_tree(paths):
    tree = tree_factory()
    for path in paths:
        subtree = tree
        for node in path:
            subtree = subtree[node]
    return tree


def tree_depth_first(tree, depth=0):
    for node in sorted(tree):
        yield (node, depth)
        yield from (tree_depth_first(tree[node], depth + 1))
