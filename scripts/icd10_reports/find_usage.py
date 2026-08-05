import csv
import json
from collections import Counter, defaultdict, namedtuple
from dataclasses import dataclass
from enum import StrEnum


class ICD10IssueType(StrEnum):
    MISSING_MODIFIER_CODE = "missing_modifier_codes"
    MOVED_CODES = "moved_codes"
    DESCRIPTION_CHANGE = "description_change"


@dataclass
class ICD10Issue:
    type: ICD10IssueType


@dataclass
class MissingModifierCodeIssue(ICD10Issue):
    code: str
    modifier_codes: list[str]


@dataclass
class MovedCodesIssue(ICD10Issue):
    title: str
    comment: str
    codes_found: list[str]
    codes_missing: list[str]
    nhs2016: list[str]
    who2019: list[str]


@dataclass
class DescriptionChangeIssue(ICD10Issue):
    code: str
    combined_2016: str
    who_2019: str


@dataclass
class CodelistWithIssues:
    url: str
    issues: list[ICD10Issue]


@dataclass
class CodeWithIssues:
    code: str
    issues: list[ICD10Issue]


inline_code = namedtuple("InlineCode", ["length", "source", "values"])


def get_issue(parent: str, type: str, **kwargs) -> ICD10Issue:
    type = ICD10IssueType(type)
    if type == ICD10IssueType.MISSING_MODIFIER_CODE:
        return MissingModifierCodeIssue(type=type, **kwargs)
    elif type == ICD10IssueType.MOVED_CODES:
        if parent == "code":
            kwargs = kwargs | {"codes_found": [], "codes_missing": []}
        return MovedCodesIssue(type=type, **kwargs)
    elif type == ICD10IssueType.DESCRIPTION_CHANGE:
        return DescriptionChangeIssue(type=type, **kwargs)
    else:
        raise ValueError(f"Unknown issue type: {type}")


def load_ehrql_codelists(
    ehrql_codelists_path="tmp/ehrql_codelists.json",
) -> tuple[dict[str, list[str]], dict[str, list[inline_code]]]:
    with open(ehrql_codelists_path) as f:
        ehrql_codelists = json.load(f)

    codelist_url = "https://www.opencodelists.org/codelist{}"
    signature_to_codelists = defaultdict(set[str])
    signature_to_inline = defaultdict(set[inline_code])
    for signature, codelist_collections in ehrql_codelists["signatures"].items():
        for collection_name, collection in codelist_collections.items():
            if collection_name == "_unused_codelists":
                for codelist in collection:
                    signature_to_codelists[signature].add(
                        codelist_url.format(codelist[0])
                    )
                continue
            for codelists in collection.values():
                for codelist in codelists:
                    codelist_id = codelist[0]
                    if codelist_id == "<inline>":
                        _, length, source, values = codelist
                        signature_to_inline[signature].add(
                            inline_code(
                                length=length.replace("length=", ""),
                                source=source.replace("source=", ""),
                                values=tuple(values.replace("values=", "").split("|")),
                            )
                        )
                    signature_to_codelists[signature].add(
                        codelist_url.format(codelist[0])
                    )

    project_to_codelists = defaultdict(list)
    project_to_inline = defaultdict(list)
    for project, signatures in ehrql_codelists["projects"].items():
        for signature in signatures.values():
            project_to_codelists[project].extend(
                list(signature_to_codelists.get(signature, set()))
            )
            project_to_inline[project].extend(
                list(signature_to_inline.get(signature, set()))
            )
    return project_to_codelists, project_to_inline


def load_issues(issues_path="tmp/issues.json"):
    with open(issues_path) as f:
        issues = json.load(f)
    return [
        CodelistWithIssues(
            url=codelist,
            issues=[
                get_issue(**(issue | {"parent": "codelist"}))
                for issue in codelist_issues
            ],
        )
        for codelist, codelist_issues in issues["codelists"].items()
    ], [
        CodeWithIssues(
            code=code,
            issues=[get_issue(**(issue | {"parent": "code"})) for issue in code_issues],
        )
        for code, code_issues in issues["codes"].items()
    ]


def match_used_codelists(
    codelist_issues: list[CodelistWithIssues], ehrql_codelists: dict[str, list[str]]
) -> dict[str, list[CodelistWithIssues]]:
    codelist_issues_dict = {codelist.url: codelist for codelist in codelist_issues}
    affected_codelists_by_project = defaultdict(list)
    for project, codelists in ehrql_codelists.items():
        for codelist in codelists:
            if codelist in codelist_issues_dict:
                affected_codelists_by_project[project].append(
                    codelist_issues_dict[codelist]
                )

    return affected_codelists_by_project


def match_used_inline(
    code_issues: list[CodeWithIssues], ehrql_inline: dict[str, list[inline_code]]
) -> dict[str, list[CodeWithIssues]]:
    affected_inline_codes_by_project = defaultdict(list)
    code_issues_dict = {code.code: code for code in code_issues}
    for project, inline_codes in ehrql_inline.items():
        for inline_code in inline_codes:
            values = inline_code.values
            for code in values:
                if code in code_issues_dict:
                    affected_inline_codes_by_project[project].append(
                        code_issues_dict[code]
                    )

    return affected_inline_codes_by_project


def report_codelist_issues(
    affected_codelists_by_project: dict[str, list[CodelistWithIssues]],
):
    print(
        "Total projects with codelists with issues:", len(affected_codelists_by_project)
    )
    print("Affected codelists by project:")
    for project, codelists in affected_codelists_by_project.items():
        print(f"{project}: {len(codelists)} codelists affected")
    print("Issue types encountered:")
    issue_counter = Counter()
    for codelists in affected_codelists_by_project.values():
        for codelist in codelists:
            for issue in codelist.issues:
                issue_counter.update([issue.type])
    print(issue_counter)
    print("\n")


def report_inline_code_issues(
    affected_inline_codes_by_project: dict[str, list[CodeWithIssues]],
):
    print(
        "Total projects with inline codes with issues:",
        len(affected_inline_codes_by_project),
    )
    print("Affected inline codes by project:")
    for project, code_issues in affected_inline_codes_by_project.items():
        print(f"{project}: {len(code_issues)} inline codes affected")
    print("Issue types encountered in inline codes:")
    issue_counter = Counter()
    for code_issues in affected_inline_codes_by_project.values():
        for code in code_issues:
            for issue in code.issues:
                issue_counter.update([issue.type])
    print(issue_counter)
    print("\n")


def write_affected_csv(
    affected_codelists_by_project: dict[str, list[CodelistWithIssues]],
    affected_inline_codes_by_project: dict[str, list[CodeWithIssues]],
):
    combined = set(affected_codelists_by_project.keys()) | set(
        affected_inline_codes_by_project.keys()
    )

    headers = [
        "project",
        "codelist",
        "codelist_issues",
        "inline_codes",
        "inline_issues",
    ]
    with open("tmp/affected_projects.csv", "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=headers,
            quotechar='"',
            quoting=csv.QUOTE_ALL,
        )
        writer.writeheader()
        for project in combined:
            codelist_issues = affected_codelists_by_project.get(project, [])
            code_issues = affected_inline_codes_by_project.get(project, [])
            for codelist in codelist_issues:
                writer.writerow(
                    {
                        "project": project,
                        "codelist": codelist.url,
                        "codelist_issues": ",".join(
                            {str(issue.type) for issue in codelist.issues}
                        ),
                        "inline_codes": "",
                        "inline_issues": "",
                    }
                )
            if code_issues:
                writer.writerow(
                    {
                        "project": project,
                        "codelist": "",
                        "codelist_issues": "",
                        "inline_codes": ",".join(
                            {code_issue.code for code_issue in code_issues}
                        ),
                        "inline_issues": ",".join(
                            {
                                str(issue.type)
                                for code_issue in code_issues
                                for issue in code_issue.issues
                            }
                        ),
                    }
                )


def main():
    codelist_issues, code_issues = load_issues()
    ehrql_codelists, ehrql_inline = load_ehrql_codelists()
    affected_codelists_by_project = match_used_codelists(
        codelist_issues, ehrql_codelists
    )
    affected_inline_codes_by_project = match_used_inline(code_issues, ehrql_inline)
    report_codelist_issues(affected_codelists_by_project)
    report_inline_code_issues(affected_inline_codes_by_project)

    write_affected_csv(affected_codelists_by_project, affected_inline_codes_by_project)


if __name__ == "__main__":
    main()
