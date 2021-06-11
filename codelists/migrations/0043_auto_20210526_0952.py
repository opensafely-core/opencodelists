# Generated by Django 3.2.3 on 2021-05-26 09:52

from django.db import migrations

from opencodelists.csv_utils import csv_data_to_rows

from ..coding_systems import CODING_SYSTEMS
from ..hierarchy import Hierarchy


def set_cached_hierarchy(apps, schema_editor):
    CachedHierarchy = apps.get_model("codelists", "CachedHierarchy")
    CodelistVersion = apps.get_model("codelists", "CodelistVersion")

    for version in CodelistVersion.objects.all():
        print(version.codelist.handles.get().slug, version.id)

        coding_system = CODING_SYSTEMS[version.codelist.coding_system_id]
        if version.csv_data:
            if not hasattr(coding_system, "ancestor_relationships"):
                continue

            headers, *rows = csv_data_to_rows(version.csv_data)

            for header in ["CTV3ID", "CTV3Code", "ctv3_id", "snomedct_id", "id"]:
                if header in headers:
                    ix = headers.index(header)
                    break
            else:
                if version.codelist.handles.get().slug == "ethnicity":
                    ix = 1
                else:
                    ix = 0

            codes = tuple(sorted({row[ix] for row in rows}))
            hierarchy = Hierarchy.from_codes(coding_system, codes)

        else:
            code_to_status = dict(version.code_objs.values_list("code", "status"))
            hierarchy = Hierarchy.from_codes(coding_system, list(code_to_status))

        CachedHierarchy.objects.create(version=version, data=hierarchy.data_for_cache())


class Migration(migrations.Migration):

    dependencies = [
        ("codelists", "0042_cachedhierarchy"),
    ]

    operations = [migrations.RunPython(set_cached_hierarchy)]