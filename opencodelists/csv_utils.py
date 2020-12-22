import csv
from io import StringIO


def csv_data_to_rows(csv_data):
    return list(csv.reader(StringIO(csv_data)))


def rows_to_csv_data(rows):
    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerows(rows)
    return buf.getvalue()


def dict_rows_to_csv_data(headers, rows):
    buf = StringIO()
    writer = csv.DictWriter(buf, headers)
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()
