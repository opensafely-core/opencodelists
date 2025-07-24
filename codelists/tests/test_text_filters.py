import pytest

from codelists.templatetags.text_filters import truncatelines


@pytest.mark.parametrize(
    "input_text,max_lines,expected",
    [
        ("a\nb\nc\nd\ne", 3, "a\nb\nc"),
        ("one line only", 4, "one line only"),
        ("x\ny", 1, "x"),
        ("", 2, ""),
        ("line1\nline2\nline3", 10, "line1\nline2\nline3"),
    ],
)
def test_truncatelines_basic(input_text, max_lines, expected):
    assert truncatelines(input_text, max_lines) == expected


def test_truncatelines_default():
    text = "1\n2\n3\n4\n5"
    assert truncatelines(text) == "1\n2\n3\n4"


def test_truncatelines_invalid_max_lines():
    text = "1\n2\n3\n4\n5"
    assert truncatelines(text, "notanumber") == "1\n2\n3\n4"
