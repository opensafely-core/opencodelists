import os
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import structlog
from django.db import transaction
from openpyxl import load_workbook

from .models import Mapping


logger = structlog.get_logger()


def import_data(filename):
    def load_records():
        wb = load_workbook(filename=filename)
        rows = wb.active.rows

        headers = next(rows)
        assert headers[1].value == "VMP / VMPP/ AMP / AMPP"
        assert headers[2].value == "BNF Code"
        assert headers[4].value == "SNOMED Code"

        for row in rows:
            dmd_type = row[1].value
            bnf_code = row[2].value
            dmd_code = row[4].value

            if not bnf_code or not dmd_code:
                continue

            # In older versions of the spreadsheet, we have seen large numeric codes
            # prefixed with a single quote, presumably to stop them being rounded.
            assert bnf_code[0] != "'"
            assert dmd_code[0] != "'"

            yield [dmd_code, dmd_type, bnf_code]

    with transaction.atomic():
        Mapping.objects.all().delete()
        Mapping.objects.bulk_create(
            Mapping(dmd_code=r[0], dmd_type=r[1], bnf_concept_id=r[2])
            for r in load_records()
        )


def import_release(release_zipfile):
    with TemporaryDirectory() as tempdir:
        release_zip = ZipFile(str(release_zipfile))
        logger.info("Extracting", release_zip=release_zip.filename)
        release_zip.extractall(path=tempdir)
        import_data(os.path.join(tempdir, release_zipfile.replace(".zip", ".xlsx")))
