# Generated by Django 2.2.11 on 2020-04-29 12:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("readv2", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="concepthierarchy",
            name="child",
        ),
        migrations.RemoveField(
            model_name="concepthierarchy",
            name="parent",
        ),
        migrations.RemoveField(
            model_name="concepttermmapping",
            name="concept",
        ),
        migrations.RemoveField(
            model_name="concepttermmapping",
            name="term",
        ),
        migrations.DeleteModel(
            name="Concept",
        ),
        migrations.DeleteModel(
            name="ConceptHierarchy",
        ),
        migrations.DeleteModel(
            name="ConceptTermMapping",
        ),
        migrations.DeleteModel(
            name="Term",
        ),
    ]
