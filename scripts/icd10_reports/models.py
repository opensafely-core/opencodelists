from dataclasses import dataclass, field
from urllib.parse import quote

from opencodelists.hash_utils import hash as hash_id


@dataclass(frozen=True)
class ReportOwner:
    kind: str
    identifier: str
    name: str
    email: str | None = None
    organisation: str | None = None


@dataclass(frozen=True)
class AffectedCodelist:
    name: str
    slug: str
    user_id: str | None
    organisation_id: str | None
    version_id: int
    version_tag: str | None
    codes: frozenset[str]
    description_changes: dict[str, dict[str, str]]
    moved_code_sets: list[dict[str, object]]
    missing_modifier_codes: dict[str, frozenset[str]] = field(default_factory=dict)

    def version_paths(self) -> list[str]:
        """Return URL paths for every public identifier for this version."""
        if self.user_id:
            codelist_path = f"/codelist/user/{quote(self.user_id)}/{quote(self.slug)}/"
        else:
            codelist_path = (
                f"/codelist/{quote(self.organisation_id or '')}/{quote(self.slug)}/"
            )
        identifiers = [hash_id(self.version_id, "CodelistVersion")]
        if self.version_tag:
            identifiers.append(self.version_tag)
        return [f"{codelist_path}{quote(identifier)}/" for identifier in identifiers]

    def path(self) -> str:
        """Return the preferred URL path for links shown to users."""
        paths = self.version_paths()
        return paths[-1] if self.version_tag else paths[0]
