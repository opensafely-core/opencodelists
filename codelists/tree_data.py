"""Module for building tree data structures from coding system hierarchies."""


def build_tree_data(child_map, code_to_term, code_to_status, tree_tables):
    """
    Builds a hierarchical tree structure from coding system data.

    Args:
        child_map: Dictionary mapping codes to their children
        code_to_term: Dictionary mapping codes to their terms
        code_to_status: Dictionary mapping codes to their status (+ or -)
        tree_tables: List of (title, codes) tuples for each tree section

    Returns:
        List of dictionaries, each containing a title and its associated tree of codes.
        Each node in the tree contains:
        - id: the code
        - name: the term associated with the code
        - status: whether the code is included (+) or excluded (-)
        - children: sorted list of child nodes
        - depth: the node's depth in the tree
    """

    def process_node(code, depth=0):
        """
        Recursively processes a code and its children to build a tree node.

        Args:
            code: The code to process
            depth: The current depth in the tree (defaults to 0 for root nodes)

        Returns:
            A dictionary representing the node and its children
        """

        children = [process_node(child, depth + 1) for child in child_map.get(code, [])]

        return {
            "id": code,
            "name": code_to_term[code],
            "status": code_to_status[code],
            "children": sorted(children, key=lambda x: x["name"]),
            "depth": depth,
        }

    return [
        {"title": title, "children": [process_node(code) for code in children]}
        for title, children in tree_tables
    ]
