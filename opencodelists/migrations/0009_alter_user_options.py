# Generated by Django 4.1.3 on 2023-02-17 11:05

from django.db import migrations
import django.db.models.functions.text


class Migration(migrations.Migration):

    dependencies = [
        ("opencodelists", "0008_alter_user_username"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="user",
            options={"ordering": (django.db.models.functions.text.Lower("username"),)},
        ),
    ]
