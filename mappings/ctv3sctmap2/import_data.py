import csv
import glob
import os
import sqlite3

from django.db import connection as django_connection


def import_data(release_dir):
    """
    Import NHSD CTV3 -> SNOMED concept maps
    """
    paths = glob.glob(
        os.path.join(
            release_dir,
            "Mapping Tables",
            "Updated",
            "Clinically Assured",
            "ctv3sctmap2*.txt",
        )
    )
    assert len(paths) == 1

    with open(paths[0]) as f:
        reader = csv.DictReader(f, delimiter="\t")

        values = list(iter_values(reader))

    # UPSERT rows based on ID, using effective date to decide if a row should
    # overwrite an existing one.
    query = """
    INSERT INTO ctv3sctmap2_mapping(
        id,
        ctv3_concept_id,
        ctv3_term_id,
        ctv3_term_type,
        sct_concept_id,
        sct_description_id,
        map_status,
        effective_date,
        is_assured)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
      map_status=excluded.map_status,
      effective_date=excluded.effective_date,
      is_assured=excluded.is_assured
    WHERE excluded.effective_date > ctv3sctmap2_mapping.effective_date;
    """

    # execute the query above for each row from the release data
    connection_params = django_connection.get_connection_params()
    connection = sqlite3.connect(**connection_params)
    connection.executemany(query, values)
    connection.commit()
    connection.close()


def iter_values(rows):
    """
    Convert the given rows into an iterable of values for upserting to the DB.
    """
    for r in rows:
        # ignore SNOMED Concept and Description IDs when the Concept ID is _DRUG
        sct_concept = r["SCT_CONCEPTID"] if r["SCT_CONCEPTID"] != "_DRUG" else None
        sct_description = (
            r["SCT_DESCRIPTIONID"] if r["SCT_CONCEPTID"] != "_DRUG" else None
        )

        yield [
            r["MAPID"].strip("{}-"),
            r["CTV3_CONCEPTID"],
            r["CTV3_TERMID"],
            r["CTV3_TERMTYPE"],
            sct_concept,
            sct_description,
            r["MAPSTATUS"] == "1",
            parse_date(r["EFFECTIVEDATE"]),
            r["IS_ASSURED"] == "1",
        ]


def parse_date(s):
    return "-".join([s[:4], s[4:6], s[6:]])
