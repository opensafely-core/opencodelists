from contextlib import contextmanager


@contextmanager
def assert_difference(fn, *, expected_difference, args=None, kwargs=None):
    """Assert that the value of fn(*args, **kwargs) changes by expected_difference after
    yielding.

    Usage:

    with assert_difference(Model.objects.count, expected_difference=1):
        Model.objects.create()
    """

    args = args or ()
    kwargs = kwargs or {}

    value_before = fn(*args, **kwargs)
    yield
    value_after = fn(*args, **kwargs)

    assert value_after - value_before == expected_difference


@contextmanager
def assert_no_difference(fn, args=None, kwargs=None):
    """Assert that the value of fn(*args, **kwargs) does not change after yielding."""

    with assert_difference(fn, args=args, kwargs=kwargs, expected_difference=0):
        yield
