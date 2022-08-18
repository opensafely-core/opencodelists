from openpyxl import load_workbook

from .models import Mapping


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

    Mapping.objects.bulk_create(
        Mapping(dmd_code=r[0], dmd_type=r[1], bnf_concept_id=r[2])
        for r in load_records()
    )
