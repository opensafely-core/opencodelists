from django.db import DEFAULT_DB_ALIAS, connections

from codelists.coding_systems import CODING_SYSTEMS


def query(sql, params=None, database=None):
    database = database or DEFAULT_DB_ALIAS
    with connections[database].cursor() as c:
        c.execute(sql, params)
        return c.fetchall()


class CodingSystemReleaseRouter:
    """
    A router to ensure coding system models always use a named release database.

    In order to maintain historical releases of Coding Systems, each new release is
    imported into a separate sqlite database, recorded as a CodingSystemRelease
    (see coding_systems.versioning.models.CodingSystemRelease).  The database for a
    coding system release is identified by <coding_system>_<release_name>_<valid_from date>
    e.g. "snomedct_v1_20221001", and any Django ORM commands that access coding
    system models are expected to make use of the `using` argument to specify the
    corresponding release database that should be used
    e.g. `Concept.objects.using("snomedct_v1_20221001").filter(...)`.

    For the most part, coding system databases are read-only, and for read queries, the
    `using` argument bypasses this router, by directly specifying which database to read from.

    However, writes for coding system models (typically only during data imports and tests) do
    go via the router.  In this case, the `hints` will contain an `instance`, which is either the
    model instance being created/saved or the foreign key relationship being created/modified
    (see https://docs.djangoproject.com/en/dev/topics/db/multi-db/#hints).  For a coding system
    model, the instance will have a release database assigned to it, which is the database we return
    for the write operation.

    This router also serves to prevent database migrations on models that they should not
    have access to.  i.e. migrations for snomedct models are only allowed for databases whose
    aliases are in the form `snomedct_...`.  Any models that are not in coding sytem apps will
    be allowed to migrate in the default database only.  This means that coding system databases
    ONLY contain their relevant tables, and the default database ONLY contains non-coding system
    tables.
    """

    def _get_db_from_instance(self, model, **hints):
        if model._meta.app_label in CODING_SYSTEMS:
            if "instance" in hints and hints["instance"]._state.db is not None:
                if hints["instance"]._state.db.startswith(model._meta.app_label):
                    return hints["instance"]._state.db
                raise ValueError(
                    f'"{model._meta.app_label}" models must select a valid version database '
                    f'with a `using` argument. {hints["instance"]._state.db} is not a valid '
                    f'database for {hints["instance"]}'
                )
            raise ValueError(
                f'"{model._meta.app_label}" models must be accessed with a `using` argument '
                "(specifying the relevant coding system release database to use). "
            )
        # return None,to defer to the default router for all other models
        return None

    def db_for_read(self, model, **hints):
        return self._get_db_from_instance(model, **hints)

    def db_for_write(self, model, **hints):
        return self._get_db_from_instance(model, **hints)

    def allow_relation(self, obj1, obj2, **hints):
        # As a general rule, relations are only allowed within the same database
        # Exceptions are allowed for Mapping models, which are intended to hold
        # mappings between coding system objects in different coding systems (and
        # therefore different databases).

        # If the dbs match, relations are always allowed
        if obj1._state.db == obj2._state.db:
            return True
        # Relations between Mapping models and coding system models are allowed
        obj_models = [obj1._meta.model_name, obj2._meta.model_name]
        if "mapping" in obj_models:
            other_app_label = next(
                (
                    obj._meta.app_label
                    for obj in [obj1, obj2]
                    if obj._meta.model_name != "mapping"
                ),
                None,
            )
            # it's unlikely, but possible, that at some point there could be Mapping models
            # that have FKs to other Mapping models. In that case, `other_app_label` would be None.
            # We can ignore that and let the default router handle it.
            if other_app_label is not None:  # pragma: no cover
                return other_app_label in CODING_SYSTEMS
        # Defer to the default router for anything else
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Coding system databases are named <coding_system>_<release_name>_<valid_from date>
        # e.g. snomedct_v1_20221101
        # Migrations are only allowed for coding system models for matching databases
        # (i.e. databases with aliases that start with the coding system app label)
        # For all other app models, migrations are only allowed for the default database
        if app_label in CODING_SYSTEMS:
            return db.startswith(app_label)
        return db == DEFAULT_DB_ALIAS
