# Generated by Django 3.2.3 on 2021-05-25 09:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("codelists", "0041_alter_codelistversion_status"),
    ]

    operations = [
        migrations.CreateModel(
            name="CachedHierarchy",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("data", models.TextField()),
                (
                    "version",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cached_hierarchy",
                        to="codelists.codelistversion",
                    ),
                ),
            ],
        ),
    ]
