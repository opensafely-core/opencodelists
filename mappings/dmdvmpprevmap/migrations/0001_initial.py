# Generated by Django 4.1.3 on 2022-12-08 15:02

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Mapping",
            fields=[
                (
                    "id",
                    models.CharField(max_length=18, primary_key=True, serialize=False),
                ),
                ("vpidprev", models.CharField(max_length=18)),
            ],
        ),
    ]
