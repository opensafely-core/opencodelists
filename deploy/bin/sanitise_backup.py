import base64
import hashlib
import secrets

import argparse
import faker
import sqlean as sqlite3

ALGORITHM = "pbkdf2_sha256"

def hash_password(password, salt=None, iterations=2000):
    # https://til.simonwillison.net/python/password-hashing-with-pbkdf2
    if salt is None:
        salt = secrets.token_hex(16)
    assert salt and isinstance(salt, str) and "$" not in salt
    assert isinstance(password, str)
    pw_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
    )
    b64_hash = base64.b64encode(pw_hash).decode("ascii").strip()
    return "{}${}${}${}".format(ALGORITHM, iterations, salt, b64_hash)

def main(backup_file):
    fake = faker.Faker()
    conn = sqlite3.connect(backup_file)

    # Get a list of all tables excluding sqlite system tables and versioning table
    # as these do not contain user, or user-supplied data.
    cur = conn.execute("""
                       SELECT name
                       FROM sqlite_schema
                       WHERE type ='table'
                       AND name NOT LIKE 'sqlite_%'
                       AND name NOT LIKE 'versioning_%';""")
    tables = [t[0] for t in cur.fetchall()]

    # Find tables that have foreign keys that reference the user table
    # and tables that contain user-supplied freetext data.
    # Django admin log entires may reference user objects but do not have
    # the requisite FKs so add manually.
    references_user = [
        ("object_id","django_admin_log"),
        ("object_repr","django_admin_log"),]
    contains_user_freetext = {}
    for table in tables:
        cur = conn.execute(f"PRAGMA foreign_key_list('{table}')")
        fks = cur.fetchall()
        references_user.extend([(fk[3],table) for fk in fks if fk[2]=="opencodelists_user" and fk[4]=="username"])

        # Django system tables do not have user-supplied freetexts
        if table.startswith("django_"):
            continue
        cur = conn.execute(f"PRAGMA table_info({table});")
        columns = cur.fetchall()
        # Find text columns excluding "data", e.g. codelist csv data
        text_columns = [c[1] for c in columns if c[2].lower() == "text" and "data" not in c[1]]
        if text_columns:
            contains_user_freetext[table] = text_columns

    # Sanitise user data and related
    cur = conn.execute("select username from opencodelists_user;")
    usernames = [row[0] for row in cur.fetchall()]
    fake_usernames = []
    for username in usernames:
        # "deferrable" FKs means we can break integrity within a transaction
        statements=["BEGIN TRANSACTION"]

        # Generate fake username that's not a real username or one we've already had
        while True:
            fake_username = fake.user_name()
            if fake_username not in fake_usernames and fake_username not in usernames:
                fake_usernames.append(fake_username)
                break;
        fake_name = fake.name()
        fake_email = f"{username}@example.com"
        fake_password = hash_password(fake.password())

        # Update FK fields (must be done first)
        for user_column, table in references_user:
            statements.append(f"UPDATE {table} SET {user_column} = '{fake_username}' WHERE {user_column} = '{username}'")

        # Update user fields containing personal data
        statements.append(f"""
                     UPDATE opencodelists_user
                     SET username = '{fake_username}',
                        name = '{fake_name}',
                        email = '{fake_email}',
                        password = '{fake_password}'
                    WHERE username = '{username}'""")

        statements.append("COMMIT TRANSACTION")

        conn.executescript(";\n".join(statements)+";\n")


    # Sanitise freetext fields
    for table, columns in contains_user_freetext.items():
        for column in columns:
            stmt = f"UPDATE {table} SET {column} = '[freetext removed]' WHERE COALESCE({column},'') <> '';"
            conn.execute(stmt)

    # Replace API keys
    cur = conn.execute("SELECT key FROM authtoken_token;")
    keys = [k[0] for k in cur.fetchall()]
    for key in keys:
        conn.execute(
            f"UPDATE authtoken_token SET key = '{secrets.token_hex(20)}' WHERE key = '{key}';"
        )

    # Remove Django sessions
    conn.execute("DELETE FROM django_session")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("backup_file", help="Path to sqlite3 file to be sanitised, which will be overwritten.")
    args = parser.parse_args()
    main(args.backup_file)
