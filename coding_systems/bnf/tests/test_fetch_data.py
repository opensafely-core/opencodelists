from unittest.mock import patch

from coding_systems.bnf.fetch_data import get_latest_bnf_release_metadata_from_odp_api


@patch("coding_systems.bnf.fetch_data.requests.get")
def test_get_latest_bnf_release_metadata_success(mocked_get):
    # create a mock object for the get request response
    mocked_response = mocked_get.return_value
    # create another mock object for returned obj from response.json()
    mocked_response.json.return_value = {
        "result": {
            "resources": [
                {
                    "name": "BNF_CODE_CURRENT_202503_VERSION_88",
                    "url": "https://example.com/download/bnf_code_current_202503_version_88.csv",
                },
                {
                    "name": "BNF_CODE_CURRENT_202607_VERSION_90_FINAL",
                    "url": "https://example.com/download/bnf_code_current_202607_version_90.csv",
                },
                {
                    "name": "BNF_CODE_CURRENT_202608_VERSION_90",
                    "url": "https://example.com/download/bnf_code_current_202608_version_90.csv",
                },
            ]
        }
    }

    latest_bnf_release_info = get_latest_bnf_release_metadata_from_odp_api()

    mocked_get.assert_called_once_with(
        "https://opendata.nhsbsa.net/api/3/action/package_show?id=bnf-code-information-current-year",
        timeout=10,
    )

    assert latest_bnf_release_info == {
        "name": "BNF_CODE_CURRENT_202608_VERSION_90",
        "date": "202608",
        "version": "90",
        "url": "https://example.com/download/bnf_code_current_202608_version_90.csv",
    }
