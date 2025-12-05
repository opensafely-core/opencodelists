# Delete codelists without handles, see https://github.com/opensafely-core/opencodelists/issues/2893
from django.db import migrations


def delete_codelists_without_handles(apps, schema_editor):
    """Delete codelists that have no associated handles."""
    Codelist = apps.get_model('codelists', 'Codelist')
    codelists_without_handles = Codelist.objects.filter(handles__isnull=True)
    # Deletes via CASCADE bypassing ORM `delete``methods.
    deleted_stats = codelists_without_handles.delete()

    # Provide some feedback.
    try:
        deleted_count = deleted_stats[1]['codelists.Codelist']
        print(f"0001: Deleted {deleted_count} codelists without handles")
    except KeyError:
        print("0001: No codelists without handles to delete")

class Migration(migrations.Migration):

    dependencies = [
        ('codelists', '0063_alter_handle_name'),
    ]

    operations = [
        migrations.RunPython(
            delete_codelists_without_handles,
            migrations.RunPython.noop
        ),
    ]
