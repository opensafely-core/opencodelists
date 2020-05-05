from django.db import connection


def query(sql, params=None):
    with connection.cursor() as c:
        c.execute(sql, params)
        return c.fetchall()
