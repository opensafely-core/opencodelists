import csv
import json


def run(in_path, out_path):
    """Create JSON file containing data about PRIMIS vaccine uptake reporting codelists.

    Data comes from a CSV file, which comes from copying and pasting tables from a
    document into a spreadsheet.
    """

    with open(in_path) as f:
        rows = list(csv.reader(f))

    records = []
    record = {}

    grab_next_row = False

    for row in rows[1:]:
        row = [c for ix, c in enumerate(row) if ix == 0 or c]
        if len(row) == 1:
            continue

        if grab_next_row:
            if not row[0]:
                assert len(row) == 2
                title = row[1]
                if title[0] == "(":
                    assert title[-1] == ")"
                    title = title[1:-1]
                record["title"] = title
            grab_next_row = False

        if row[0] and row[0] != "Note":
            if row[1].endswith("_COD") or row[1] in ["BMI_STAGE", "SEV_OBESITY"]:
                assert len(row) == 4

                if record:
                    records.append(record)

                record = {
                    "id": row[0],
                    "name": row[1],
                    "details": row[2],
                    "criteria": row[3],
                    "title": None,
                }

                if row[0] == "36":
                    record["title"] = "BMI"

                grab_next_row = True

    records.append(record)

    for record in records:
        for k, v in record.items():
            record[k] = v.replace("–", "-")

    with open(out_path) as f:
        json.dump(records, f, indent=2)
