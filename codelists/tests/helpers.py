from io import BytesIO

from codelists import tree_utils


def csv_builder(contents):
    """
    Build a CSV from the given contents

    When testing CSVs in views and forms we need to replicate an uploaded CSV,
    this does that with the use of BytesIO.
    """
    buffer = BytesIO()
    buffer.write(contents.encode("utf8"))
    buffer.seek(0)
    return buffer


def build_tree():
    r"""Return tree with this structure:

           a
          / \
         b   c
        / \ / \
       d   e   f
      / \ / \ / \
     g   h   i   j

    (This is actually a DAG.)
    """

    edges = [
        ("a", "b"),
        ("a", "c"),
        ("b", "d"),
        ("b", "e"),
        ("c", "e"),
        ("c", "f"),
        ("d", "g"),
        ("d", "h"),
        ("e", "h"),
        ("e", "i"),
        ("f", "i"),
        ("f", "j"),
    ]
    paths = tree_utils.edges_to_paths("a", edges)
    return tree_utils.paths_to_tree(paths)
