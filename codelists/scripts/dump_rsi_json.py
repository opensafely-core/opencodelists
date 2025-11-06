import json
import re
from collections import Counter
from enum import Enum, auto

from django.db.models import Q

from codelists.models import Codelist, CodelistVersion, Handle, Status
from opencodelists.hash_utils import unhash
from opencodelists.models import Organisation, User


CODELIST_URL_MARKDOWN_PAT = re.compile(r"\([^\)]+codelist\/[^\)]+\)")
CLONE_SOURCE_URL_PAT = re.compile(r"(Cloned from codelist : \[[^\]]+\]\()([^\)]+)")


class CreationMethod(Enum):
    UPLOADED = auto()
    BUILDER = auto()
    CONVERTED = auto()
    CLONED = auto()
    EMPTY = auto()
    UNKNOWN = auto()


def get_version_from_url_parts(url_split: list[str]) -> CodelistVersion | None:
    """
    Work from right to left, trying to find a CodelistVersion by tag or hash in URL
    """
    for url_component in reversed(url_split):
        tagged_versions = CodelistVersion.objects.filter(tag=url_component)
        if tagged_versions:
            if codelist := get_codelist_from_url_parts(url_split):
                try:
                    return tagged_versions.get(codelist=codelist)
                except CodelistVersion.DoesNotExist:
                    ...
        try:
            id = unhash(url_component, "CodelistVersion")
            return CodelistVersion.objects.get(id=id)
        except (ValueError, CodelistVersion.DoesNotExist):
            continue


def get_codelist_from_url_parts(url_split: list[str]) -> Codelist | None:
    """
    Work from left to right, try to get codelist from owner and slug in URL
    """
    owner_is_user = False
    owner = None
    slug = None
    for url_component in url_split[url_split.index("codelist") + 1 :]:
        if url_component == "user":
            owner_is_user = True
            continue
        if not owner:
            owner = url_component
            continue
        if not slug:
            slug = url_component
            break
    if owner_is_user:
        try:
            owner = User.objects.get(username=owner)
        except User.DoesNotExist:
            return False
    else:
        try:
            owner = Organisation.objects.get(slug=owner)
        except Organisation.DoesNotExist:
            return False
    owner_query = Q(user=owner) if isinstance(owner, User) else Q(organisation=owner)
    try:
        handle = Handle.objects.get(owner_query & Q(slug=slug))
        return handle.codelist
    except Handle.DoesNotExist:
        return None


def is_bnf(version_url: str) -> bool:
    url_split = version_url.split("/")
    if version := get_version_from_url_parts(url_split):
        return version.codelist.coding_system_id == "bnf"
    if codelist := get_codelist_from_url_parts(url_split):
        return codelist.coding_system_id == "bnf"
    return False


def references_bnf_codelist(codelist: Codelist) -> bool:
    for reference in codelist.references.filter(
        url__contains="opencodelists.org/codelist"
    ):
        if is_bnf(reference.url):
            return True
    return False


def linked_bnf_in_methodology(methodology: str) -> bool:
    if methodology:
        # new standard formatting
        if "Converted from [pseudo-BNF system codelist]" in methodology:
            return True
        # try to find other links in variable old formats
        for match in re.findall(CODELIST_URL_MARKDOWN_PAT, methodology):
            if is_bnf(match):
                return True
    return False


def creation_method(version: CodelistVersion) -> CreationMethod:
    if (
        version.codelist.methodology
        and "Cloned from codelist" in version.codelist.methodology
    ):
        return CreationMethod.CLONED
    if version.coding_system_id == "dmd" and (
        linked_bnf_in_methodology(version.codelist.methodology)
        or references_bnf_codelist(version.codelist)
    ):
        return CreationMethod.CONVERTED
    if version.searches.exists():
        # One could conceivably delete all searches in builder,
        # and then we couldn't tell the difference between built and uploaded.
        # This is hopefully quite rare
        return CreationMethod.BUILDER
    if version.csv_data or version.code_objs.exists():
        return CreationMethod.UPLOADED
    if len(version.codes) == 0:
        return CreationMethod.EMPTY
    return CreationMethod.UNKNOWN


def get_clone_source_creation_method(version: CodelistVersion) -> CreationMethod | None:
    if not version.codelist.methodology:
        return
    match = CLONE_SOURCE_URL_PAT.match(version.codelist.methodology)
    if not match:
        return
    cloned_url = match.groups()[1]
    cloned_version = get_version_from_url_parts(cloned_url.split("/"))
    if cloned_version:
        return creation_method(cloned_version)


def run():
    """
    Export every Codelist which has at least one Published or Under Review version,
    except a known broked codelist with no associated Handles,
    and all of their Published or Under Review CodelistVersion.

    The CreationMethod of each CodelistVersion is inferred,
    as this is not explicitly stored anywhere in the database.

    If a CodelistVersion is found to be created by cloning,
    infer the CreationMethod of the clone source and add it to the output too.

    Summary statistics of the export are printed to the console.
    """
    codelists = [
        {
            "name": codelist.name,
            "owner": str(codelist.current_handle.owner),
            "coding_system": codelist.coding_system_id,
            "slug": codelist.full_slug(),
            "created_at": str(codelist.created_at),
            "updated_at": str(codelist.updated_at),
            "versions": [
                {
                    "tag": version.tag,
                    "hash": version.hash,
                    "slug": version.full_slug(),
                    "created_at": str(version.created_at),
                    "updated_at": str(version.updated_at),
                    "coding_system_release": str(version.coding_system_release),
                    "author": str(version.author),
                    "status": version.status,
                    "creation_method": cm.name.title()
                    if (cm := creation_method(version))
                    else None,
                    "clone_source_creation_method": ccm.name.title()
                    if (ccm := get_clone_source_creation_method(version))
                    else None,
                }
                for version in codelist.versions.filter(
                    status__in=[Status.PUBLISHED, Status.UNDER_REVIEW]
                )
            ],
        }
        for codelist in Codelist.objects.filter(~Q(id=10907))
        # 10907 has no handles and breaks everything
        if codelist.versions.filter(status__in=[Status.PUBLISHED, Status.UNDER_REVIEW])
    ]

    versions = [
        cv for c in [codelist["versions"] for codelist in codelists] for cv in c
    ]
    creation_methods = Counter([version["creation_method"] for version in versions])
    coding_systems = Counter([codelist["coding_system"] for codelist in codelists])

    print(f"""
    Codelists: {len(codelists)}
    Versions: {len(versions)}

    Coding systems:
    {coding_systems}

    Creation methods:
    {creation_methods}

    """)

    with open("rsi-codelists-analysis.json", "w") as f:
        json.dump(codelists, f, indent=4)
