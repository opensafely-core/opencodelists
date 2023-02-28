import re

from ..base.trud_utils import TrudDownloader


class Downloader(TrudDownloader):

    item_number = 101
    # snomedct release files are in the format uk_sct2cl_35.5.0_20230215000001Z.zip
    # where the release name is 35.5.0
    # The release date is found in the metadata and is not usually identical to the date
    # in the file
    release_regex = re.compile(r"^uk_sct2cl_(?P<release>\d+\.\d+\.\d+)_20\d{12}Z\.zip$")
    coding_system_id = "snomedct"
