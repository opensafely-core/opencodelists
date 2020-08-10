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


def build_tree(depth=4):
    r"""Return balanced binary tree.

    Nodes are labelled so that node i has children (2 * i) and (2 * i + 1).

    For depth=4, a tree with the following structure is returned:

           ┌-----1-----┐
           |           |
        ┌--2--┐     ┌--3--┐
        |     |     |     |
      ┌-4-┐ ┌-5-┐ ┌-6-┐ ┌-7-┐
      |   | |   | |   | |   |
      8   9 10 11 12 13 14 15
    """

    paths = [
        [str(2 ** j + (i >> (depth - 1 - j))) for j in range(depth)]
        for i in range(2 ** (depth - 1))
    ]
    return tree_utils.paths_to_tree(paths)
