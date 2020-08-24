from hypothesis import given, settings
from hypothesis import strategies as st

from codelists.definition import Definition, build_codes, build_rows, codes_from_query
from codelists.hierarchy import Hierarchy
from codelists.tree_utils import edges_to_paths, paths_to_tree
from dummy_coding_system import build_dummy_coding_system


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


def test_roundtrip_examples(subtests):
    # tree has this structure:
    #
    #      ┌--0--┐
    #      |     |
    #   ┌--1--┌--2--┐
    #   |     |     |
    # ┌-3-┐ ┌-4-┐ ┌-5-┐
    # |   | |   | |   |
    # 6   7 8   9 10 11

    edges = [
        ("0", "1"),
        ("0", "2"),
        ("1", "3"),
        ("1", "4"),
        ("2", "4"),
        ("2", "5"),
        ("3", "6"),
        ("3", "7"),
        ("4", "8"),
        ("4", "9"),
        ("5", "10"),
        ("5", "11"),
    ]
    hierarchy = Hierarchy("0", edges)

    for codes, query in [
        # # the root element
        # ({"0"}, ["0"]),
        # # an intermediate element
        # ({"2"}, ["2"]),
        # # a leaf element
        # ({"8"}, ["8"]),
        # # everything under intermediate element, inclusive
        # ({"2", "4", "5", "8", "9", "10", "11"}, ["2<"]),
        # # everything under intermediate element, exclusive
        # ({"4", "5", "8", "9", "10", "11"}, ["4<", "5<"]),
        # # everything under intermediate element, except another intermediate element
        # ({"2", "5", "8", "9", "10", "11"}, ["2<", "~4"]),
        # # everything under intermediate element, except leaf element
        # ({"2", "4", "5", "9", "10", "11"}, ["2<", "~8"]),
        # everything under root element, except intermediate element and its children (i)
        ({"0", "1", "2", "3", "4", "6", "7", "8", "9"}, ["0", "1<", "2"]),
        # everything under root element, except intermediate element and its children (ii)
        ({"0", "1", "2", "3", "5", "6", "7", "10", "11"}, ["0", "1", "2", "3<", "5<"],),
    ]:
        code_to_name = {e: f"name_{e}" for _, e in edges}
        code_to_name = {"0": "name_0", **code_to_name}

        coding_system = build_dummy_coding_system(tree=tree)

        with subtests.test(codes=codes, query=query):
            defn1 = Definition.from_codes(codes, hierarchy)
            assert sorted(str(r) for r in defn1.rules) == sorted(query)
            assert defn1.codes(hierarchy) == codes

            defn2 = Definition.from_query(query)
            assert sorted(str(r) for r in defn2.rules) == sorted(query)
            assert defn2.codes(hierarchy) == codes

            # print(f"codes: {codes}, query: {query}")
            # definition = Definition.from_codes(code_to_name, codes, tree)
            # assert sorted(str(e) for e in definition.elements) == sorted(query)

            # output = build_codes(
            #     definition.included_elements(), definition.excluded_elements(), tree
            # )
            # assert output == codes

            # # TODO: need to get a dummy coding_system here
            # output = set(codes_from_query(coding_system, query))
            # assert output == codes


@settings(deadline=None)
@given(hierarchies(24), st.sets(st.sampled_from(range(16))), st.floats(0.1, 0.5))
def test_roundtrip(hierarchy, codes, r):
    definition = Definition.from_codes(codes, hierarchy, r)
    assert definition.codes(hierarchy) == codes

    fragments = [rule.fragment for rule in definition.rules]
    assert len(fragments) == len(set(fragments))

    definition_codes = [rule.code for rule in definition.rules]
    assert len(definition_codes) == len(set(definition_codes))


def test_definition_from_dag():
    # build up a DAG from our typical edges graph
    # turn that into a defintion
    # render as rows?
    pass


def test_dummy_edges():
    # pytest -s codelists/tests/test_definition.py::test_all_except_intermediate_and_children

    edges = [
        ("0", "1"),
        ("0", "2"),
        ("1", "3"),
        ("1", "4"),
        ("2", "4"),
        ("2", "5"),
        ("3", "6"),
        ("3", "7"),
        ("4", "8"),
        ("4", "9"),
        ("5", "10"),
        ("5", "11"),
    ]
    paths = edges_to_paths("0", edges)
    tree = paths_to_tree(paths)

    coding_system = build_dummy_coding_system(edges=edges, tree=tree)
    codes = {"0", "1", "2", "3", "4", "6", "7", "8", "9"}

    ancestor_relationships = coding_system.ancestor_relationships(codes)
    print(ancestor_relationships)
    descendant_relationships = coding_system.descendant_relationships(codes)
    print(descendant_relationships)
    edges = ancestor_relationships + descendant_relationships

    expected = [
        ("0", "1"),
        ("0", "2"),
        ("1", "3"),
        ("1", "4"),
        ("2", "4"),
        ("2", "5"),
        ("3", "6"),
        ("3", "7"),
        ("4", "8"),
        ("4", "9"),
        ("5", "10"),
        ("5", "11"),
    ]
    assert edges == expected


def test_all_except_intermediate_and_children():
    # tree has this structure:
    #
    #      ┌--0--┐
    #      |     |
    #   ┌--1--┌--2--┐
    #   |     |     |
    # ┌-3-┐ ┌-4-┐ ┌-5-┐
    # |   | |   | |   |
    # 6   7 8   9 10 11
    edges = [
        ("0", "1"),
        ("0", "2"),
        ("1", "3"),
        ("1", "4"),
        ("2", "4"),
        ("2", "5"),
        ("3", "6"),
        ("3", "7"),
        ("4", "8"),
        ("4", "9"),
        ("5", "10"),
        ("5", "11"),
    ]
    paths = edges_to_paths("0", edges)
    tree = paths_to_tree(paths)
    codes = {"0", "1", "2", "3", "4", "6", "7", "8", "9"}
    query = ["0", "1<", "2"]

    code_to_name = {e: f"name_{e}" for _, e in edges}
    code_to_name = {"0": "name_0", **code_to_name}

    coding_system = build_dummy_coding_system(tree=tree)

    print(f"codes: {codes}, query: {query}")
    definition = Definition.from_codes(code_to_name, codes, tree)
    assert sorted(str(e) for e in definition.elements) == sorted(query)

    output = build_codes(
        definition.included_elements(), definition.excluded_elements(), tree
    )
    assert output == codes

    # TODO: need to get a dummy coding_system here
    output = set(codes_from_query(coding_system, query))
    assert output == codes


# def test_rows(subtests):
#    # tree has this structure:
#    #
#    #      ┌--0--┐
#    #      |     |
#    #   ┌--1--┌--2--┐
#    #   |     |     |
#    # ┌-3-┐ ┌-4-┐ ┌-5-┐
#    # |   | |   | |   |
#    # 6   7 8   9 10 11

#    edges = [
#        ("0", "1"),
#        ("0", "2"),
#        ("1", "3"),
#        ("1", "4"),
#        ("2", "4"),
#        ("2", "5"),
#        ("3", "6"),
#        ("3", "7"),
#        ("4", "8"),
#        ("4", "9"),
#        ("5", "10"),
#        ("5", "11"),
#    ]
#    paths = edges_to_paths("0", edges)
#    tree = paths_to_tree(paths)

#    code_to_name = {e: f"name_{e}" for _, e in edges}
#    code_to_name = {"0": "name_0", **code_to_name}

#    codes = [
#        # the root element
#        {"0"},
#        # an intermediate element
#        {"2"},
#        # a leaf element
#        {"8"},
#        # everything under intermediate element, inclusive
#        {"2", "4", "5", "8", "9", "10", "11"},
#        # everything under intermediate element, exclusive
#        {"4", "5", "8", "9", "10", "11"},
#        # everything under intermediate element, except another intermediate element
#        {"2", "5", "8", "9", "10", "11"},
#        # everything under intermediate element, except leaf element
#        {"2", "4", "5", "9", "10", "11"},
#        # everything under root element, except intermediate element and its children (i)
#        {"0", "1", "2", "3", "4", "6", "7", "8", "9"},
#        # everything under root element, except intermediate element and its children (ii)
#        {"0", "1", "2", "3", "5", "6", "7", "10", "11"},
#    ]

#    for code in codes:
#        with subtests.test(codes=codes):
#            definition = Definition.from_codes(code_to_name, codes, tree)
#            rows = build_rows(tree, definition)
#            assert len(rows) == len(definition.elements)


# @settings(deadline=None)
# @given(dags(24), st.sets(st.sampled_from(range(16))), st.floats(0.1, 0.5))
# def test_roundtrip(dag, codes, r):
#     edges = [(parent, child) for parent, children in dag.items() for child in children]
#     paths = edges_to_paths(0, edges)
#     tree = paths_to_tree(paths)
#     definition = Definition.from_codes(codes, tree, r)
#     assert definition.codes(tree) == codes

#     fragments = [e.fragment for e in definition.elements]
#     assert len(fragments) == len(set(fragments))
#     definition_codes = [e.code for e in definition.elements]
#     assert len(definition_codes) == len(set(definition_codes))
