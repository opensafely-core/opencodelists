import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from enum import Enum


class CodelistIssueType(Enum):
    MISSING_MODIFIER_CODE = "missing_modifier_codes"
    MOVED_CODES = "moved_codes"
    DESCRIPTION_CHANGE = "description_change"


@dataclass
class CodelistIssue:
    type: CodelistIssueType


@dataclass
class MissingModifierCodeIssue(CodelistIssue):
    code: str
    modifier_codes: list[str]


@dataclass
class MovedCodesIssue(CodelistIssue):
    title: str
    comment: str
    codes_found: list[str]
    codes_missing: list[str]
    nhs2016: list[str]
    who2019: list[str]


@dataclass
class DescriptionChangeIssue(CodelistIssue):
    code: str
    combined_2016: str
    who_2019: str


@dataclass
class IssueCodelist:
    url: str
    issues: list[CodelistIssue]


def get_issue(type: str, **kwargs) -> CodelistIssue:
    type = CodelistIssueType(type)
    if type == CodelistIssueType.MISSING_MODIFIER_CODE:
        return MissingModifierCodeIssue(type=type, **kwargs)
    elif type == CodelistIssueType.MOVED_CODES:
        return MovedCodesIssue(type=type, **kwargs)
    elif type == CodelistIssueType.DESCRIPTION_CHANGE:
        return DescriptionChangeIssue(type=type, **kwargs)
    else:
        raise ValueError(f"Unknown issue type: {type}")


def load_simplified_usage(
    simplified_ehrql_codelists_path="tmp/simplified_ehrql_codelists.json",
):
    with open(simplified_ehrql_codelists_path) as f:
        simplified_usage = json.load(f)
    return {
        repo: [
            f"https://www.opencodelists.org/codelist{codelist}"
            for codelist in codelists
        ]
        for repo, codelists in simplified_usage.items()
    }


def load_issue_codelists(issues_path="tmp/issues.json"):
    with open(issues_path) as f:
        issues = json.load(f)
    return {
        codelist: [get_issue(**issue) for issue in codelist_issues]
        for codelist, codelist_issues in issues["codelists"].items()
    }


def match_example_usage(issues, simplified_usage):
    affected_codelists_by_project = defaultdict(list)
    for project, codelists in simplified_usage.items():
        for codelist in codelists:
            if codelist in issues:
                affected_codelists_by_project[project].append(issues[codelist])

    return affected_codelists_by_project


def main():
    issues = load_issue_codelists()
    simplified_usage = load_simplified_usage()
    affected_codelists_by_project = match_example_usage(issues, simplified_usage)
    print("Total projects affected:", len(affected_codelists_by_project))
    print("Affected codelists by project:")
    for project, codelists in affected_codelists_by_project.items():
        print(f"{project}: {len(codelists)} codelists affected")
    print("Issue types encountered:")
    issue_counter = Counter()
    for codelists in affected_codelists_by_project.values():
        for codelist_issues in codelists:
            issue_counter.update([issue.type for issue in codelist_issues])
    print(issue_counter)

    # with open("tmp/affected_codelists_by_project.json", "w") as f:
    #     json.dump(affected_codelists_by_project, f, indent=2)


if __name__ == "__main__":
    main()
