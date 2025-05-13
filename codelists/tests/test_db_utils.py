from opencodelists import db_utils


def test_query_with_many_params():
    values = list(range(5000))
    placeholders = ["%s"] * len(values)
    sql = "SELECT 'found' WHERE %s IN ({})".format(", ".join(placeholders))
    last_value = values[-1]
    params = [last_value] + values
    result = db_utils.query(sql, params)
    assert result == [("found",)]
