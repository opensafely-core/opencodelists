import pytest
import sqlean as sqlite3
from django.db import connections, models

from deploy.bin.sanitise_backup import main as sanitise_backup
from opencodelists.models import User


@pytest.mark.django_db(transaction=True)
class TestBackupSanitisation:
    def test_user_fields_sanitised(self, universe, tmp_path):
        personal_data_fields = ["username", "email", "name", "password"]
        original_users = [v for v in universe.values() if isinstance(v, User)]

        backup_path = backup_db(tmp_path)
        sanitise_backup(backup_path)

        conn = sqlite3.connect(backup_path)
        cur = conn.execute(
            f"SELECT {','.join(personal_data_fields)} FROM opencodelists_user;"
        )
        sanitised_users = cur.fetchall()

        for original_user in original_users:
            for i, personal_data_field in enumerate(personal_data_fields):
                original_value = getattr(original_user, personal_data_field)
                sanitised_values = [s[i] for s in sanitised_users]
                assert original_value not in sanitised_values

    def test_freetexts_replaced(self, universe, tmp_path):
        fixtures_with_freetext = {
            v: [
                f.name
                for f in type(v)._meta.get_fields()
                if isinstance(f, models.TextField)
            ]
            for v in universe.values()
            if issubclass(type(v), models.Model)
            and any(
                [
                    f
                    for f in type(v)._meta.get_fields()
                    if isinstance(f, models.TextField)
                ]
            )
        }

        backup_path = backup_db(tmp_path)
        sanitise_backup(backup_path)

        conn = sqlite3.connect(backup_path)
        current_original_type = None
        for original_with_freetext, freetext_fields in fixtures_with_freetext.items():
            if not current_original_type or not isinstance(
                original_with_freetext, current_original_type
            ):
                cur = conn.execute(
                    f"SELECT {','.join(freetext_fields)} FROM {type(original_with_freetext)._meta.db_table};"
                )
                sanitised_freetexts = cur.fetchall()
            for i, freetext_field in enumerate(freetext_fields):
                if "data" in freetext_field:
                    continue
                original_value = getattr(original_with_freetext, freetext_field)
                if original_value is None or original_value == "":
                    continue
                sanitised_values = [s[i] for s in sanitised_freetexts]
                assert original_value not in sanitised_values

    def test_user_references_intact(self, universe, tmp_path):
        # _meta doesn't have a direct way of getting *only* reverse (i.e.) related fields
        # so subtract the non-reverse fields away from all fields to derive this.
        related_fields = [
            (f.accessor_name, f.related_model._meta.db_table, f.remote_field.column)
            for f in set(User._meta._get_fields(reverse=True))
            - set(User._meta._get_fields(reverse=False))
            # We will check the counts at the "via"/"through" table for any
            # many-to-many relationships.
            if not isinstance(f, models.fields.reverse_related.ManyToManyRel)
        ]

        original_users = [v for v in universe.values() if isinstance(v, User)]

        original_related_counts = {}
        for original_user in original_users:
            related_counts = {}
            for related_field in related_fields:
                # Some related attrs are created dynamically so we must check.
                if hasattr(original_user, related_field[0]):
                    related_field_value = getattr(original_user, related_field[0])

                    # Fetch count of related rows if one to many.
                    if hasattr(related_field_value, "count"):
                        related_count = related_field_value.count()
                    else:
                        related_count = 1
                else:
                    related_count = 0
                related_counts[related_field] = related_count
            original_related_counts[original_user] = related_counts

        backup_path = backup_db(tmp_path)
        sanitise_backup(backup_path)

        conn = sqlite3.connect(backup_path)

        # Check no records with pre-existing usernames
        for original_user, related_counts in original_related_counts.items():
            username = original_user.username
            for _, table, user_field in related_counts.keys():
                cur = conn.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE {user_field}='{username}';"
                )
                rowcount = cur.fetchone()[0]
                assert rowcount == 0

        # Check the number of relations matches pre-existing.
        # We can't use the fixture usernames to find relations as they've been sanitised.
        cur = conn.execute("SELECT username from opencodelists_user;")
        sanitised_usernames = [r[0] for r in cur.fetchall()]
        # Get the related count for each relation for each user
        sanitised_related_counts = {}
        for sanitised_username in sanitised_usernames:
            related_counts = {}
            for related in related_fields:
                _, table, user_field = related
                cur = conn.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE {user_field}='{sanitised_username}';"
                )
                rowcount = cur.fetchone()[0]
                related_counts[related] = rowcount
            sanitised_related_counts[username] = related_counts
        # Check the related counts for each relation for each user match
        for sanitised_relation_count_dict in sanitised_related_counts.values():
            sanitised_occurrance_count = len(
                [
                    s
                    for s in sanitised_related_counts.values()
                    if s == sanitised_relation_count_dict
                ]
            )
            original_occurrance_count = len(
                [
                    f
                    for f in original_related_counts.values()
                    if f == sanitised_relation_count_dict
                ]
            )
            assert sanitised_occurrance_count == original_occurrance_count


def backup_db(tmp_path):
    backup_path = tmp_path / "test_backup.db"
    cur = connections["default"].cursor()
    cur.execute(f"VACUUM main INTO '{backup_path}';")
    return backup_path
