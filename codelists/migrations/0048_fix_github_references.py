# Generated by Django 4.0.3 on 2022-03-15 14:55

from django.db import migrations

OLD_METHOLOLOGY = "See [code on GitHub](https://github.com/opensafely/opencodelists/blob/master/codelists/management/commands/convert_codelist.py)"
NEW_METHOLOLOGY = "See [code on GitHub](https://github.com/opensafely-core/opencodelists/blob/248fe3397327e019a2d93830bd5fdb1c2562b23d/codelists/management/commands/convert_codelist.py)"


def fix_github_references(apps, schema_editor):
    Codelist = apps.get_model("codelists", "Codelist")
    for codelist in Codelist.objects.filter(methodology=OLD_METHOLOLOGY):
        codelist.methodology = NEW_METHOLOLOGY
        codelist.save()


class Migration(migrations.Migration):

    dependencies = [
        ("codelists", "0047_auto_20220125_1404"),
    ]

    operations = [
        migrations.RunPython(
            fix_github_references, reverse_code=migrations.RunPython.noop
        ),
    ]
