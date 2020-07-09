import csv
import io
from datetime import datetime

from django.core.management import BaseCommand

from ...models import Codelist


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("path")
        parser.add_argument("cluster_id")
        parser.add_argument("project_slug")
        parser.add_argument("codelist_name")

    def handle(self, path, cluster_id, project_slug, codelist_name, **kwargs):
        with open(path) as f:
            rows = [[r[2], r[3]] for r in csv.reader(f) if r[0] == cluster_id]

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["CTV3Code", "Description"])
        writer.writerows(rows)
        csv_data = buffer.getvalue()

        Codelist.objects.create(
            project_id=project_slug,
            name=codelist_name,
            coding_system_id="ctv3tpp",
            version_str=datetime.today().strftime("%Y-%m-%d"),
            csv_data=csv_data,
            description=f"The following codes are used to indicate {codelist_name}",
            methodology=f"The following codes are prepared from CTV3 and expected to be used in general practices in records of people with {codelist_name}. They cover a broad range and some codes may no longer be in routine use. The codelists have been derived from information supporting the general practice quality and outcomes framework to support research in OpenSAFELY. Once imported they were reviewed and ....OPTIONAL x, y and z was done (remove if it was signed off)",
        )
