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

    # csv_headers is a dict of possible headers in uploaded csv_data representing the
    # code and term.  This is used to identify the code/term columns in older codelist
    # versions and versions uploaded directly from CSV
    #
    # Older codelist versions and those created by direct "old-style" CSV upload via
    # codelists/views/version_upload.py
    # may contain various headers, which may or may not be valid.
    # As of https://github.com/opensafely-core/opencodelists/pull/1459, "old-style" CSV
    # uploads are now validated to check for appropriate code headers, so the only possible
    # code headers are "code" and "dmd_id" ("dmd_id" is the code header used for BNF to dm+D
    # CSV downloads). However, we still need to accommodate older codelist versions that predate
    # this.
    #
    # Each CodingSystem inheriting from this base class defines its own set of possible
    # headers for the code and term fields.
    #
    # Note that we do not do any validation of the "term" column when CSV data is uploaded
    # CodingSystem classes define headers that have been used for this column in the past, but
    # are not guaranteed to be exhaustive in future.
    csv_headers = {"code": ["code"], "term": ["term"]}

    @classmethod
    def is_builder_compatible(self):
        return issubclass(self, BuilderCompatibleCodingSystem)

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
        assert database_alias in all_slugs, (
            f"{database_alias} is not a valid database alias for a {cls.short_name} release."
        )
        return database_alias

    @cached_property
    def release(self):
        return CodingSystemRelease.objects.get(database_alias=self.database_alias)

    @cached_property
    def release_name(self):
        return self.release.release_name

    def lookup_names(self, codes):  # pragma: no cover
        raise NotImplementedError

    def lookup_synonyms(self, codes):  # pragma: no cover
        return {}

    def lookup_references(self, codes):  # pragma: no cover
        return {}

    def code_to_term(self, codes):  # pragma: no cover
        raise NotImplementedError


class DummyCodingSystem(BaseCodingSystem):
    """
    Represents a CodingSystem that will never have an associated database.
    """

    has_database = False

    def code_to_term(self, codes):
        return {code: "unknown" for code in codes}


class BuilderCompatibleCodingSystem(BaseCodingSystem):
    """
    A base class for coding systems that implement the methods required
    by the codelist builder SPA.

    This class is used to clearly define the requirements of this interface
    and for easy identification of coding systems that implement it.
    """

    # User-facing description to be rendered in the UI
    description = NotImplemented
    # When set to true, we only show this in the builder behind a feature flag
    is_experimental = False
    # By default when displaying a hierarchy we sort the concepts by term so
    # they appear in alphabetical order. Sometimes we want to display things in
    # code order - e.g. for prefix hierarchies like ICD10 users prefer to see
    # the order E10, E11, E12 etc, rather than alphabetical
    sort_by_term = True

    def ancestor_relationships(self, codes):  # pragma: no cover
        """
        This method, in combination with `descendant_relationships`, defines
        the hierarchical structure of a codelist.

        It defines which codes should be considered ancestors/parents of the
        provided `codes`.
        """
        raise NotImplementedError

    def codes_by_type(self, codes, hierarchy):  # pragma: no cover
        """
        This method defines the top-level categorisation/typing of codes in a
        coding system and thus how they are displayed to users in the builder SPA
        """
        raise NotImplementedError

    def descendant_relationships(self, codes):  # pragma: no cover
        """
        This method, in combination with `descendant_relationships`, defines
        the hierarchical structure of a codelist.

        It defines which codes should be considered descendants/children of the
        provided `codes`.
        """
        raise NotImplementedError

    def matching_codes(self, codes):
        """
        Given a set/list of codes, return the subset of those codes
        that are found in the coding system. This is used to identify
        codes on a codelist version that have been removed in the
        current release of the coding system.
        """
        raise NotImplementedError

    def search_by_term(self, term):  # pragma: no cover
        """
        Return the codes within a coding system that match a "term"-based search,
        for example codes which contain the term within codes' names or descriptions.

        Implementation may vary from coding system to coding system according to its
        structure and the desired search logic.

        Where a coding system contains multiple entity types, this method (along with
        `search_by_code`) also defines which of those are searched and therefore eligible
        for inclusion in a codelist of that coding system.
        """
        raise NotImplementedError

    def search_by_code(self, code):  # pragma: no cover
        """
        Return the codes within a coding system that match a "code"-based search,
        which may be exact or fuzzy matched according to user requirements.

        Implementation may vary from coding system to coding system according to its
        structure and the desired search logic.

        Where a coding system contains multiple entity types, this method (along with
        `search_by_code`) also defines which of those are searched and therefore eligible
        for inclusion in a codelist of that coding system.
        """
        raise NotImplementedError
