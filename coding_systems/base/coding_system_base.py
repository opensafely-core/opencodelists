from abc import ABC

from django.utils.functional import cached_property

from coding_systems.versioning.models import CodingSystemVersion


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

    def __init__(self, database_alias):
        self.db = database_alias
        # Convenience alias attribute for retrieving the coding system version slug from
        # a CodingSystem
        self.version_slug = database_alias

    @classmethod
    def most_recent(cls):
        """
        Return a CodingSystem instance for the most recent version.
        """
        most_recent_version = CodingSystemVersion.objects.most_recent(cls.id)
        if most_recent_version is None:
            raise CodingSystemVersion.DoesNotExist(
                f"No coding system data found for {cls.short_name}"
            )
        return cls(database_alias=most_recent_version.slug)

    @classmethod
    def get_version_or_most_recent(cls, version_slug=None):
        """
        Returns a CodingSystem instance for the requested version, or the most recent one.
        """
        version_slug = cls.validate_db_alias(version_slug)
        return cls(database_alias=version_slug)

    @classmethod
    def validate_db_alias(cls, version_slug):
        """
        Ensure that this slug is associated with a valid CodingSystemVersion
        If no version_slug is provided, default to the most recent one.
        """
        if version_slug is None:
            return cls.most_recent().version_slug
        all_slugs = CodingSystemVersion.objects.filter(
            coding_system=cls.id
        ).values_list("slug", flat=True)
        assert (
            version_slug in all_slugs
        ), f"{version_slug} is not a valid database alias for a {cls.short_name} version."
        return version_slug

    @cached_property
    def version(self):
        return CodingSystemVersion.objects.get(slug=self.db)

    @cached_property
    def version_name(self):
        return self.version.version

    def search_by_term(self, term):
        raise NotImplementedError

    def search_by_code(self, code):
        raise NotImplementedError

    def lookup_names(self, codes):
        raise NotImplementedError

    def code_to_term(self, codes):
        raise NotImplementedError

    def codes_by_type(self, codes, hierarchy):
        raise NotImplementedError
