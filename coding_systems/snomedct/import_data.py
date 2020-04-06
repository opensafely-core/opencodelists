import csv
import datetime
import glob
import os
import sqlite3

from django.db import connection as django_connection

from .models import Concept, Description, Relationship


def import_data(release_dir):
    def load_records(filename):
        paths = glob.glob(
            os.path.join(
                release_dir, "Full", "Terminology", "sct2_" + filename + "*.txt"
            )
        )
        assert len(paths) == 1

        with open(paths[0]) as f:
            reader = csv.reader(f, delimiter="\t")
            next(reader)
            for r in reader:
                r[1] = parse_date(r[1])  # effective_time
                r[2] = r[2] == "1"  # active
                yield r

    connection_params = django_connection.get_connection_params()
    connection = sqlite3.connect(**connection_params)
    connection.executemany(build_sql(Concept), load_records("Concept"))
    connection.executemany(build_sql(Description), load_records("Description"))
    connection.executemany(build_sql(Relationship), load_records("StatedRelationship"))
    connection.executemany(build_sql(Relationship), load_records("Relationship"))
    connection.commit()
    connection.close()


def parse_date(datestr):
    return datetime.date(int(datestr[:4]), int(datestr[4:6]), int(datestr[6:]))


def build_sql(model):
    table_name = model._meta.db_table
    cols = ", ".join(f.attname for f in model._meta.fields)
    params = ", ".join("?" for f in model._meta.fields)
    updates = ", ".join(
        "{} = excluded.{}".format(f.attname, f.attname) for f in model._meta.fields
    )

    return """
    INSERT INTO {table_name}({cols})
      VALUES ({params})
    ON CONFLICT(id) DO UPDATE SET
      {updates}
    WHERE excluded.effective_time > {table_name}.effective_time;
    """.format(
        **locals()
    )
