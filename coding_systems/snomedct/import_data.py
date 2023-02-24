import csv
import datetime
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import structlog
from django.db import connections

from coding_systems.base.import_data_utils import CodingSystemImporter

from .data_downloader import Downloader
from .models import Concept, Description, Relationship

logger = structlog.get_logger()


def import_data(
    release_dir,
    release_name,
    valid_from,
    latest=False,
    import_ref=None,
    check_compatibility=True,
):
    downloader = Downloader(release_dir)
    release_zipfile_path = downloader.download_release(release_name, valid_from, latest)
    import_release(
        release_zipfile_path, release_name, valid_from, import_ref, check_compatibility
    )


def import_release(
    release_zipfile, release_name, valid_from, import_ref, check_compatibility
):
    import_ref = import_ref or release_zipfile.name

    with CodingSystemImporter(
        "snomedct", release_name, valid_from, import_ref, check_compatibility
    ) as database_alias:
        with TemporaryDirectory() as tempdir:
            release_zip = ZipFile(release_zipfile)
            logger.info("Extracting", release_zip=release_zip.filename)
            release_zip.extractall(path=tempdir)

            release_dir = Path(tempdir)
            release_subdir_patterns = [
                "SnomedCT_InternationalRF2_PRODUCTION_*",
                "SnomedCT_UKClinicalRF2_PRODUCTION_*",
                "SnomedCT_UKEditionRF2_PRODUCTION_*",
            ]

            connection_params = connections[database_alias].get_connection_params()
            connection = sqlite3.connect(**connection_params)
            for release_subdir_pattern in release_subdir_patterns:
                release_subdirs = list(release_dir.glob(release_subdir_pattern))
                assert len(release_subdirs) == 1
                import_models(release_subdirs[0], connection)
            connection.commit()
            connection.close


def load_records(release_subdir, filename_part):
    paths = list(
        (release_subdir / "Full" / "Terminology").glob(f"sct2_{filename_part}_*.txt")
    )
    assert len(paths) == 1
    logger.info("Loading records", filepath=str(paths[0]))

    with open(paths[0]) as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader)
        for r in reader:
            r[1] = parse_date(r[1])  # effective_time
            r[2] = r[2] == "1"  # active
            yield r


def import_models(release_subdir, connection):
    connection.executemany(build_sql(Concept), load_records(release_subdir, "Concept"))
    connection.executemany(
        build_sql(Description), load_records(release_subdir, "Description")
    )
    connection.executemany(
        build_sql(Relationship),
        load_records(release_subdir, "StatedRelationship"),
    )
    connection.executemany(
        build_sql(Relationship), load_records(release_subdir, "Relationship")
    )


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
