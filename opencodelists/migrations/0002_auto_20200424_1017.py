# Generated by Django 2.2.11 on 2020-04-24 10:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("opencodelists", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="organisation",
            name="url",
            field=models.URLField(default=""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="project",
            name="details",
            field=models.TextField(default=""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="project",
            name="url",
            field=models.URLField(default=""),
            preserve_default=False,
        ),
    ]
