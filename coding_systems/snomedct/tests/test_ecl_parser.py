import pytest

from coding_systems.snomedct.ecl_parser import ParseError, handle


examples = [
    ("111111", {(None, "111111")}, set()),
    ("<111111", {("<", "111111")}, set()),
    ("<<111111", {("<<", "111111")}, set()),
    ("111111 OR <222222", {(None, "111111"), ("<", "222222")}, set()),
    ("<111111 MINUS 333333", {("<", "111111")}, {(None, "333333")}),
    (
        "(<<111111 OR <<222222) MINUS (<<333333 OR <<444444)",
        {("<<", "111111"), ("<<", "222222")},
        {("<<", "333333"), ("<<", "444444")},
    ),
]


def test_handle(subtests):
    for expr, included, excluded in examples:
        with subtests.test(expr):
            handled = handle(expr)
            assert handled["included"] == included
            assert handled["excluded"] == excluded


def test_parse_error_syntax_error():
    with pytest.raises(ParseError):
        handle("(111111 OR 222222) MINUS (333333 OR 444444")


def test_parse_error_attempting_full_context():
    with pytest.raises(ParseError, match="Attempting full context"):
        handle("111111 < 222222")


def test_error_nested_minus_operation():
    node = {
        "type": "minus",
        "lhs": {"type": "expr", "operator": None, "value": "222222"},
        "rhs": {"type": "expr", "operator": None, "value": "333333"},
    }
    with pytest.raises(AssertionError, match=str(node)):
        handle("111111 MINUS (222222 MINUS 333333)")


def test_error_child_of():
    # Child of operator "<!" is not allowed
    with pytest.raises(AssertionError):
        handle("<!111111")
