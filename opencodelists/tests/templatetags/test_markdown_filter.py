import pytest

from opencodelists.templatetags.methodology_cloned_codelist_name_filter import (
    methodology_cloned_codelist_name_filter,
)


@pytest.mark.parametrize(
    "input,expected",
    [
        (
            "Cloned from codelist : [Codelist_to_be_cloned](/codelist/user/katieb5/codelist_to_be_cloned/2ed738d9/)\r\nSome additional methodology text",
            "Cloned from codelist : [Codelist\\_to\\_be\\_cloned](/codelist/user/katieb5/codelist_to_be_cloned/2ed738d9/)\r\nSome additional methodology text",
        ),
        (
            "Cloned from codelist : [Codelist_to_be_cloned](/codelist/user/katieb5/codelist_to_be_cloned/2ed738d9/)\r\nSome_additional_methodology_text_with_underscores",
            "Cloned from codelist : [Codelist\\_to\\_be\\_cloned](/codelist/user/katieb5/codelist_to_be_cloned/2ed738d9/)\r\nSome_additional_methodology_text_with_underscores",
        ),
        (
            "Cloned from codelist : [ClonedCodelistWithoutUnderscores](/codelist/user/katieb5/clonedcodelistwithoutunderscores/2ed738d9/)\r\nSome additional methodology text",
            "Cloned from codelist : [ClonedCodelistWithoutUnderscores](/codelist/user/katieb5/clonedcodelistwithoutunderscores/2ed738d9/)\r\nSome additional methodology text",
        ),
        (
            "Methodology text without cloned codelist",
            "Methodology text without cloned codelist",
        ),
        (
            "",
            "",
        ),
        (
            "Some other text. Cloned from codelist : [Codelist_to_be_cloned](/codelist/user/katieb5/codelist_to_be_cloned/2ed738d9/)\r\nSome additional methodology text",
            "Some other text. Cloned from codelist : [Codelist\\_to\\_be\\_cloned](/codelist/user/katieb5/codelist_to_be_cloned/2ed738d9/)\r\nSome additional methodology text",
        ),
    ],
    ids=[
        "cloned_codelist_with_underscores",
        "cloned_codelist_with_underscores_and_underscored_following_text",
        "cloned_codelist_without_underscores",
        "no_cloned_codelist_prefix",
        "empty_string",
        "cloned_codelist_not_at_start_of_text",
    ],
)
def test_methodology_cloned_codelist_name_filter(input, expected):
    assert methodology_cloned_codelist_name_filter(input) == expected
