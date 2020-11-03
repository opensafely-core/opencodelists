from io import BytesIO

from hypothesis import strategies as st

from codelists.hierarchy import Hierarchy


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


def build_small_hierarchy():
    r"""Return hierarchy with this structure:

        a
       / \
      b   c
     / \ / \
    d   e   f
    """

    edges = [
        ("a", "b"),
        ("a", "c"),
        ("b", "d"),
        ("b", "e"),
        ("c", "e"),
        ("c", "f"),
    ]

    return Hierarchy("a", edges)


def build_hierarchy():
    r"""Return hierarchy with this structure:

           a
          / \
         b   c
        / \ / \
       d   e   f
      / \ / \ / \
     g   h   i   j
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

    return Hierarchy("a", edges)


@st.composite
def hierarchies(draw, size):
    """Build a Hierarchy with `size` nodes.

    Based on an indea by @Zac-HD at https://github.com/HypothesisWorks/hypothesis/issues/2464.
    """

    edges = []
    for child_id in range(1, size):
        for parent_id in draw(st.sets(st.sampled_from(range(child_id)), min_size=1)):
            edges.append((parent_id, child_id))
    return Hierarchy("0", edges)
