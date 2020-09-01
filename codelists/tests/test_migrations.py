from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


# We use TransactionTestCase because "SQLite schema editor cannot be used while
# foreign key constraint checks are enabled".  I haven't spent any time working
# out how to work around this.
class TestMigration0006(TransactionTestCase):
    migrate_from = [("codelists", "0004_auto_20200722_1437")]
    migrate_to = [("codelists", "0007_auto_20200722_1438")]

    def test_forwards(self):
        executor = MigrationExecutor(connection)
        old_apps = executor.loader.project_state(self.migrate_from).apps
        new_apps = executor.loader.project_state(self.migrate_to).apps
        OldCodelist = old_apps.get_model("codelists", "Codelist")
        NewCodelist = new_apps.get_model("codelists", "Codelist")

        executor.migrate(self.migrate_from)

        Project = old_apps.get_model("opencodelists", "Project")
        project = Project.objects.create(name="Test")

        old_cl = OldCodelist.objects.create(
            project=project,
            name="Test",
            version_str="2020-07-19",
            csv_data="code,description",
        )

        executor.loader.build_graph()
        executor.migrate(self.migrate_to)

        new_cl = NewCodelist.objects.get(pk=old_cl.pk)
        new_clv = new_cl.versions.order_by("version_str").last()
        self.assertEqual(new_clv.version_str, "2020-07-19")
        self.assertEqual(new_clv.csv_data, "code,description")
        self.assertFalse(new_clv.is_draft)

    def test_backwards(self):
        executor = MigrationExecutor(connection)
        old_apps = executor.loader.project_state(self.migrate_from).apps
        new_apps = executor.loader.project_state(self.migrate_to).apps
        OldCodelist = old_apps.get_model("codelists", "Codelist")
        NewCodelist = new_apps.get_model("codelists", "Codelist")

        Project = new_apps.get_model("opencodelists", "Project")
        project = Project.objects.create(name="Test")

        new_cl = NewCodelist.objects.create(project=project, name="Test")
        new_cl.versions.create(version_str="2020-07-19", csv_data="code,description")

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)

        old_cl = OldCodelist.objects.get(pk=new_cl.pk)
        self.assertEqual(old_cl.version_str, "2020-07-19")
        self.assertEqual(old_cl.csv_data, "code,description")
