from django.db import DEFAULT_DB_ALIAS, connections


def query(sql, params=None, database=None):
    database = database or DEFAULT_DB_ALIAS
    with connections[database].cursor() as c:
        c.execute(sql, params)
        return c.fetchall()
