import re

from ..base.trud_utils import TrudDownloader


class Downloader(TrudDownloader):

    item_number = 24
    # dm+d release files are in the format nhsbsa_dmd_9.1.0_20220912000001.zip
    # where the release name is 9.1.0 and the release date is 2022-09-12
    # the first digit in the release name is the non-zero padded month, in
    # this case September - 9 - and the following digits are for major and
    # minor releases in that month
    release_regex = re.compile(
        r"^nhsbsa_dmd_(?P<release>([1-9]|1[0-2])\.[\d+]\.[\d+])_(?P<year>20\d{2})(?P<month>0[1-9]|1[0-2])(?P<day>(0[1-9]|[12]\d|3[01]))0+1\.zip$"
    )
    coding_system_id = "dmd"

    def get_release_name_from_release_metadata(self, metadata):
        return f'{metadata["valid_from"].year} {metadata["release"]}'
