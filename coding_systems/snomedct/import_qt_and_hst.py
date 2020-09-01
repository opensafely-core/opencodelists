import csv
import glob
import os
import sqlite3

from django.db import connection as django_connection

from .models import HistorySubstitution, QueryTableRecord


def import_data(release_dir):
    def load_query_table_records():
        paths = glob.glob(
            os.path.join(release_dir, "Resources", "QueryTable", "xres2_*.txt")
        )
        assert len(paths) == 1, paths

        with open(paths[0]) as f:
            reader = csv.reader(f, delimiter="\t")
            next(reader)
            yield from reader

    def load_history_substitution_table_recods():
        paths = glob.glob(
            os.path.join(
                release_dir, "Resources", "HistorySubstitutionTable", "xres2_*.txt"
            )
        )
        assert len(paths) == 1, paths

        with open(paths[0]) as f:
            reader = csv.reader(f, delimiter="\t")
            next(reader)
            for r in reader:
                r[5] = r[5] == "1"  # is_ambiguous
                r[11] = r[11] == "1"  # tlh_identical_flag
                r[12] = r[12] == "1"  # fsn_tagless_identical_flag
                r[13] = r[13] == "1"  # fsn_tag_identical_flag
                yield r

    connection_params = django_connection.get_connection_params()
    connection = sqlite3.connect(**connection_params)
    connection.executemany(build_sql(QueryTableRecord), load_query_table_records())
    connection.executemany(
        build_sql(HistorySubstitution), load_history_substitution_table_recods()
    )
    connection.commit()
    connection.close()


def build_sql(model):
    table_name = model._meta.db_table
    cols = ", ".join(f.attname for f in model._meta.fields if not f.primary_key)
    params = ", ".join("?" for f in model._meta.fields if not f.primary_key)
    return f"INSERT INTO {table_name}({cols}) VALUES ({params})"
