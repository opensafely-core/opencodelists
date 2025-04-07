from django.db import connections


def backup(backup_path, connection=connections["default"]):
    cur = connection.cursor()
    cur.execute(f"VACUUM main INTO '{backup_path}';")
