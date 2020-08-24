import pytest
from django.core.management import call_command

from codelists.tree_utils import edges_to_paths, paths_to_tree


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass


@pytest.fixture(scope="session")
def snomed_tennis_elbow(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("loaddata", "coding_systems/snomedct/fixtures/tennis-elbow.json")


@pytest.fixture(scope="function")
def dummy_tree():
    """
    Builds a dummy tree structure:

           ┌--0--┐
           |     |
        ┌--1--┌--2--┐
        |     |     |
      ┌-3-┐ ┌-4-┐ ┌-5-┐
      |   | |   | |   |
      6   7 8   9 10 11

    """
    edges = [
        ("0", "1"),
        ("0", "2"),
        ("1", "3"),
        ("1", "4"),
        ("2", "4"),
        ("2", "5"),
        ("3", "6"),
        ("3", "7"),
        ("4", "8"),
        ("4", "9"),
        ("5", "10"),
        ("5", "11"),
    ]

    paths = edges_to_paths("0", edges)

    return paths_to_tree(paths)
