from .helpers import build_small_hierarchy


def test_nodes():
    hierarchy = build_small_hierarchy()

    assert hierarchy.nodes == {"a", "b", "c", "d", "e", "f"}


def test_parent_map():
    hierarchy = build_small_hierarchy()

    assert len(hierarchy.parent_map) == 5
    for node, children in {
        "b": {"a"},
        "c": {"a"},
        "d": {"b"},
        "e": {"b", "c"},
        "f": {"c"},
    }.items():
        assert hierarchy.parent_map[node] == children


def test_child_map():
    hierarchy = build_small_hierarchy()

    assert len(hierarchy.child_map) == 3
    for node, parents in {
        "a": {"b", "c"},
        "b": {"d", "e"},
        "c": {"e", "f"},
    }.items():
        assert hierarchy.child_map[node] == parents


def test_ancestors():
    hierarchy = build_small_hierarchy()

    for node, ancestors in {
        "a": set(),
        "b": {"a"},
        "c": {"a"},
        "d": {"a", "b"},
        "e": {"a", "b", "c"},
        "f": {"a", "c"},
    }.items():
        assert hierarchy.ancestors(node) == ancestors


def test_descendants():
    hierarchy = build_small_hierarchy()

    for node, descendants in {
        "a": {"b", "c", "d", "e", "f"},
        "b": {"d", "e"},
        "c": {"e", "f"},
        "d": set(),
        "e": set(),
        "f": set(),
    }.items():
        assert hierarchy.descendants(node) == descendants
