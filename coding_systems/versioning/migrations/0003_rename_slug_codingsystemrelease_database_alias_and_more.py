# Generated by Django 4.1.2 on 2022-11-04 15:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("versioning", "0002_rename_codingsystemversion_codingsystemrelease"),
    ]

    operations = [
        migrations.RenameField(
            model_name="codingsystemrelease",
            old_name="slug",
            new_name="database_alias",
        ),
        migrations.RenameField(
            model_name="codingsystemrelease",
            old_name="version",
            new_name="release_name",
        ),
        migrations.AlterUniqueTogether(
            name="codingsystemrelease",
            unique_together={("coding_system", "release_name", "valid_from")},
        ),
    ]