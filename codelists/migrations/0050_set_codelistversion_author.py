# Generated by Django 4.0.3 on 2022-03-17 11:16

from django.db import migrations


def set_author_from_draft_owner(apps, schema_editor):
    CodelistVersion = apps.get_model("codelists", "CodelistVersion")
    versions_with_draft_owner = CodelistVersion.objects.filter(
        draft_owner__isnull=False
    )
    for version in versions_with_draft_owner:
        version.author = version.draft_owner
        version.save()


def revert_to_draft_owner(apps, schema_editor):
    CodelistVersion = apps.get_model("codelists", "CodelistVersion")
    draft_versions = CodelistVersion.objects.filter(status="draft")
    for version in draft_versions:
        version.draft_owner = version.author
        version.save()


class Migration(migrations.Migration):

    dependencies = [
        ("codelists", "0049_codelistversion_author"),
    ]

    operations = [
        migrations.RunPython(
            set_author_from_draft_owner, reverse_code=revert_to_draft_owner
        )
    ]
