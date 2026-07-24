from dataclasses import dataclass
from urllib.parse import quote

from opencodelists.hash_utils import hash as hash_id


@dataclass(frozen=True)
class ReportOwner:
    kind: str
    identifier: str
    name: str
    email: str | None = None


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

    def path(self) -> str:
        if self.user_id:
            codelist_path = f"/codelist/user/{quote(self.user_id)}/{quote(self.slug)}/"
        else:
            codelist_path = (
                f"/codelist/{quote(self.organisation_id or '')}/{quote(self.slug)}/"
            )
        tag_or_hash = self.version_tag or hash_id(self.version_id, "CodelistVersion")
        return f"{codelist_path}{quote(tag_or_hash)}/"
