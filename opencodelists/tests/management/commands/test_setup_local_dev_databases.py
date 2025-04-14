import pytest
from django.core.management import call_command

from opencodelists.management.commands import setup_local_dev_databases


def test_setup_local_dev_databases_exits_early_when_in_prod_environment(monkeypatch):
    monkeypatch.setattr(setup_local_dev_databases, "in_production", lambda: True)

    with pytest.raises(SystemExit) as error:
        call_command("setup_local_dev_databases")

    assert error.value.code == 1
