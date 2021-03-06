# Generated by Django 3.1.7 on 2021-04-23 11:16

from django.db import migrations


def update_slugs(apps, schema_editor):
    Search = apps.get_model("codelists", "Search")
    for search in Search.objects.filter(code__isnull=False):
        search.slug = f"code:{search.code}"
        search.save()


class Migration(migrations.Migration):

    dependencies = [
        ("codelists", "0031_auto_20210413_0829"),
    ]

    operations = [migrations.RunPython(update_slugs)]
