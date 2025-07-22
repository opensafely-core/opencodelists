"""
WSGI config for opencodelists project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "opencodelists.settings")

application = get_wsgi_application()


# Ensure that the coding system database connections are updated. This needs to
# be run once at startup. Previously, it was executed during the AppConfig
# ready method, but Django warned us against it because you shouldn't access
# the database in that method: (https://github.com/opensafely-core/opencodelists/issues/2289)
# We can't import the method at the top of the file because it would create a
# circular import, so we import it here instead. For reference, the circular
# import is:
# - coding_system/versioning/models.py imports from codelists.coding_systems,
# - which dynamically imports modules like coding_systems.snomedct.coding_system,
# - which imports from coding_system_base.py,
# - which imports back from coding_systems.versioning.models.
def run_startup_tasks():
    from coding_systems.versioning.models import (
        update_coding_system_database_connections,
    )

    update_coding_system_database_connections()


run_startup_tasks()
