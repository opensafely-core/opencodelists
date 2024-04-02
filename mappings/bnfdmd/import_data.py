import pandas as pd
from django.db import transaction

from .models import Mapping


def import_data(filename):
    def load_records():
        column_names = {
            "VMP / VMPP/ AMP / AMPP": "dmd_type",
            "BNF Code": "bnf_code",
            "SNOMED Code": "dmd_code",
        }
        # This will fail with ValueError if the columns don't match.
        df = pd.read_excel(
            io=filename,
            dtype=object,
            usecols=column_names.keys(),
        )

        df = df.rename(columns=column_names)
        df = df.dropna(subset=["bnf_code", "dmd_code"])

        # In older versions of the spreadsheet, we have seen large numeric codes
        # prefixed with a single quote, presumably to stop them being rounded.
        assert "'" not in df["bnf_code"].str[0].values
        assert "'" not in df["dmd_code"].str[0].values

        return df.itertuples(index=False)

    with transaction.atomic():
        Mapping.objects.all().delete()
        Mapping.objects.bulk_create(
            Mapping(dmd_code=r.dmd_code, dmd_type=r.dmd_type, bnf_concept_id=r.bnf_code)
            for r in load_records()
        )
