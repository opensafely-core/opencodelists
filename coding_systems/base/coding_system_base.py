from abc import ABC

from django.utils.functional import cached_property

from coding_systems.versioning.models import CodingSystemRelease


class BaseCodingSystem(ABC):
    """
    A base class for coding systems.
    A CodingSystem is intended to be the interface to a coding system, and represents
    a single version of a specific coding system.
    No models contained within coding_system apps (including the `versioning` app)
    should be accessed directly.
    """

    id = NotImplemented
    name = NotImplemented
    short_name = NotImplemented
    root = None
    # flag to indicate that this CodingSystem is associated with a real database instance
    has_database = True

    def __init__(self, database_alias):
        self.database_alias = database_alias

    @classmethod
    def get_by_release_or_most_recent(cls, database_alias=None):
        """
        Returns a CodingSystem instance for the requested release, or the most recent one.
        """
        if database_alias is None:
            most_recent_release = CodingSystemRelease.objects.most_recent(cls.id)
            if most_recent_release is None:
                raise CodingSystemRelease.DoesNotExist(
                    f"No coding system data found for {cls.short_name}"
                )
            return cls(database_alias=most_recent_release.database_alias)
        database_alias = cls.validate_db_alias(database_alias)
        return cls(database_alias=database_alias)

    @classmethod
    def get_by_release(cls, database_alias):
        """
        Returns a CodingSystem instance for the requested release
        """
        assert database_alias is not None
        return cls.get_by_release_or_most_recent(database_alias)

    @classmethod
    def validate_db_alias(cls, database_alias):
        """
        Ensure that this database_alias is associated with a valid CodingSystemRelease
        that is ready to use (i.e. not in "importing" state)
        """
        all_slugs = (
            CodingSystemRelease.objects.ready()
            .filter(coding_system=cls.id)
            .values_list("database_alias", flat=True)
        )
        assert (
            database_alias in all_slugs
        ), f"{database_alias} is not a valid database alias for a {cls.short_name} release."
        return database_alias

    @cached_property
    def release(self):
        return CodingSystemRelease.objects.get(database_alias=self.database_alias)

    @cached_property
    def release_name(self):
        return self.release.release_name

    def search_by_term(self, term):  # pragma: no cover
        raise NotImplementedError

    def search_by_code(self, code):  # pragma: no cover
        raise NotImplementedError

    def lookup_names(self, codes):  # pragma: no cover
        raise NotImplementedError

    def code_to_term(self, codes):  # pragma: no cover
        raise NotImplementedError

    def codes_by_type(self, codes, hierarchy):  # pragma: no cover
        raise NotImplementedError


class DummyCodingSystem(BaseCodingSystem):
    """
    Represents a CodingSystem that will never have an associated database.
    """

    has_database = False
