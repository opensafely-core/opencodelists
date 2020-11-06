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

            if bnf_code is None or dmd_code is None:
                continue
            if bnf_code == "'" or dmd_code == "'":
                continue
            if isinstance(bnf_code, str):
                bnf_code = bnf_code.lstrip("'")
            if isinstance(dmd_code, str):
                dmd_code = dmd_code.lstrip("'")

            yield [dmd_code, dmd_type, bnf_code]

    Mapping.objects.bulk_create(
        Mapping(dmd_code=r[0], dmd_type=r[1], bnf_concept_id=r[2])
        for r in load_records()
    )
