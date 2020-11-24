from codelists import presenters
from codelists.definition import Definition
from codelists.hierarchy import Hierarchy


class DummyCodingSystem:
    def lookup_names(self, names):
        return {name: name for name in names}


def test_build_definition_rows():
    # hierarchy has this structure:
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

    # construct a hierarchy with 2, and all its descendants except 8
    definition = Definition.from_codes({"2", "4", "5", "9", "10", "11"}, hierarchy)

    # make a dummy coding system so we can do name lookup
    dummy_coding_system = DummyCodingSystem()

    rows = presenters.build_definition_rows(dummy_coding_system, hierarchy, definition)

    # we expect only one row (with an exclusion for 8)
    assert len(rows) == 1

    row = rows[0]
    assert row["code"] == "2"
    assert row["all_descendants"]

    # the only excluded code should be 8
    assert len(row["excluded_descendants"]) == 1
    excluded = row["excluded_descendants"][0]
    assert excluded["code"] == "8"
