import pytest
import sqlean as sqlite3
from django.db import connections, models
from rest_framework.authtoken.models import Token

from deploy.bin.sanitise_backup import main as sanitise_backup
from opencodelists.models import User


@pytest.mark.django_db(transaction=True)
class TestBackupSanitisation:
    """
    These use the `universe` fixture as convenient way of getting
    a realistic set of related model objects.
    There are some weird behaviours and apparent poor isolation
    between tests with regards to the in-memory model states and
    the database state.
    These tests care deeply about the latter and so employ some
    strategies to ensure it is as expected before running the
    sanitisation.
    These include iterating over the universe fixture rather than
    instantiating new models/using the model Managers, and in some
    cases explicitly saving model objects to the db that would
    otherwise could have been assumed to be saved there.
    """

    def test_api_keys_removed(self, universe, tmp_path):
        original_users = [v for v in universe.values() if isinstance(v, User)]

        # Other tests may modify the api_tokens in the db, so save the in-memory users to db
        # and create new tokens for a subset of them.
        for i, user in enumerate(original_users):
            user.save()
            if i % 2 == 0:
                Token.objects.filter(user=user).delete()
                Token.objects.create(user=user)

        api_tokens = {u.api_token for u in original_users if u.api_token}

        backup_path = backup_db(tmp_path)

        conn = sqlite3.connect(backup_path)
        cur = conn.execute("SELECT key FROM authtoken_token;")
        sanitised_tokens = {k[0] for k in cur.fetchall()}

        assert api_tokens.isdisjoint(sanitised_tokens)

    def test_user_fields_sanitised(self, universe, tmp_path):
        personal_data_fields = ["username", "email", "name", "password"]
        original_users = [v for v in universe.values() if isinstance(v, User)]

        backup_path = backup_db(tmp_path)

        conn = sqlite3.connect(backup_path)
        cur = conn.execute(
            f"SELECT {','.join(personal_data_fields)} FROM opencodelists_user;"
        )
        sanitised_users = cur.fetchall()

        for i, personal_data_field in enumerate(personal_data_fields):
            original_values = {
                getattr(original_user, personal_data_field)
                for original_user in original_users
            }
            sanitised_values = {user[i] for user in sanitised_users}
            assert original_values.isdisjoint(sanitised_values)

    def test_freetexts_replaced(self, universe, tmp_path):
        """
        Test that all Text typed fields in fixtures (where populated)
        have been replaced with sanitised values.
        """

        # Find fields within fixtures that have a Text datatype
        # and are populated.
        fixtures_with_freetext = {
            fixture: [
                field.name
                for field in type(fixture)._meta.get_fields()
                if isinstance(field, models.TextField) and "data" not in field.name
            ]
            for fixture in universe.values()
            if issubclass(type(fixture), models.Model)
            and any(
                [
                    field
                    for field in type(fixture)._meta.get_fields()
                    if isinstance(field, models.TextField) and "data" not in field.name
                ]
            )
        }

        backup_path = backup_db(tmp_path)

        conn = sqlite3.connect(backup_path)
        for original_fixture, freetext_fields in fixtures_with_freetext.items():
            cur = conn.execute(
                f"""SELECT  {",".join(freetext_fields)}
                FROM {original_fixture._meta.db_table}
                WHERE {original_fixture._meta.pk.name} = {original_fixture.pk};"""
            )
            sanitised_freetexts = set(cur.fetchall())
            original_freetexts = {
                getattr(original_fixture, freetext_field)
                for freetext_field in freetext_fields
            }

            assert sanitised_freetexts.isdisjoint(original_freetexts)

    def test_user_references_intact(self, universe, tmp_path):
        """
        Test that objects owned by users before sanitisation are still owned by them after.

        Since the User PK is username and is itself sanitised, we cannot match pre- and post-
        sanitised user records to check the other objects they own.
        Therefore, a "signature" of the user based on counts of each type of related object
        is created and compared instead.
        """

        # Find objects that have an FK relationship to User,
        # the User field that accesses the related objects,
        # the db table name for the related object and its field that refers to the User table.
        #
        # N.B. _meta doesn't have a direct way of getting *only* reverse (i.e.) related fields
        # so subtract the non-reverse fields away from all fields to derive this.
        user_fk_relationships = [
            (f.accessor_name, f.related_model._meta.db_table, f.remote_field.column)
            for f in set(User._meta._get_fields(reverse=True))
            - set(User._meta._get_fields(reverse=False))
            # We will check the counts at the "via"/"through" table for any
            # many-to-many relationships.
            if not isinstance(f, models.fields.reverse_related.ManyToManyRel)
        ]

        original_users = [v for v in universe.values() if isinstance(v, User)]

        original_related_object_counts = {}
        for original_user in original_users:
            related_counts = {}
            for related_field, _, _ in user_fk_relationships:
                # Some related attrs are created dynamically so we must check they exist.
                if hasattr(original_user, related_field):
                    related_field_value = getattr(original_user, related_field)

                    # Fetch count of related rows if one to many.
                    if hasattr(related_field_value, "count"):
                        related_count = related_field_value.count()
                    else:
                        related_count = 1
                else:
                    related_count = 0
                related_counts[related_field] = related_count
            original_related_object_counts[original_user] = related_counts

        backup_path = backup_db(tmp_path)

        conn = sqlite3.connect(backup_path)

        cur = conn.execute("SELECT username from opencodelists_user;")
        sanitised_usernames = [r[0] for r in cur.fetchall()]

        # Get the related count for each relation for each user
        sanitised_related_object_counts = {}
        for sanitised_username in sanitised_usernames:
            related_counts = {}
            for related_field, table, user_field in user_fk_relationships:
                cur = conn.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE {user_field}='{sanitised_username}';"
                )
                rowcount = cur.fetchone()[0]
                related_counts[related_field] = rowcount
            sanitised_related_object_counts[sanitised_username] = related_counts

        # Check the number of times a "signature" of related object counts appears
        # in the sanitised data matches the original.
        for sanitised_relation_count_dict in sanitised_related_object_counts.values():
            sanitised_occurrence_count = len(
                [
                    s
                    for s in sanitised_related_object_counts.values()
                    if s == sanitised_relation_count_dict
                ]
            )
            original_occurrence_count = len(
                [
                    f
                    for f in original_related_object_counts.values()
                    if f == sanitised_relation_count_dict
                ]
            )
            assert sanitised_occurrence_count == original_occurrence_count


def backup_db(tmp_path):
    backup_path = tmp_path / "test_backup.db"
    cur = connections["default"].cursor()
    cur.execute(f"VACUUM main INTO '{backup_path}';")
    sanitise_backup(backup_path)
    return backup_path
