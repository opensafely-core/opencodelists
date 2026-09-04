"""Minimal data and GitHub helpers for the portable report generator."""

import base64
import csv
import json
import re
import subprocess
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote


PORT_DIR = Path(__file__).parent


@dataclass(frozen=True)
class InputPaths:
    directory: Path

    def file(self, filename: str) -> Path:
        return self.directory / filename


DEFAULT_INPUT_PATHS = InputPaths(PORT_DIR / "data")


def parse_value(value):
    """Parse a count, treating suppressed values such as ``<15`` as zero."""
    if value.startswith("<"):
        return 0
    try:
        return int(value)
    except ValueError:
        return 0


def load_usage_data(_data_source="apcs", input_paths: InputPaths = DEFAULT_INPUT_PATHS):
    """Load the APCS primary- and all-diagnosis counts used in reports."""
    usage = defaultdict(lambda: defaultdict(int))
    with input_paths.file("code_usage_combined_apcs.csv").open() as file:
        for row in csv.DictReader(file):
            code = row.get("icd10_code", "").strip()
            if code:
                for field in ("apcs_primary_count", "apcs_all_count"):
                    usage[code][(field, "TOTAL")] += parse_value(row.get(field, ""))
    return usage, {}


def load_cache(input_paths: InputPaths = DEFAULT_INPUT_PATHS):
    cache_file = input_paths.file("github_code_search_cache.json")
    if not cache_file.exists():
        return {}
    try:
        with cache_file.open() as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return {}


def save_cache(cache, input_paths: InputPaths = DEFAULT_INPUT_PATHS):
    cache_file = input_paths.file("github_code_search_cache.json")
    try:
        input_paths.directory.mkdir(parents=True, exist_ok=True)
        with cache_file.open("w") as file:
            json.dump(cache, file, indent=2)
        print(f"\nCache saved to {cache_file}")
    except OSError as error:
        print(f"WARNING: Could not save cache: {error}")


def run_gh_command(args):
    """Run an authenticated GitHub CLI command."""
    try:
        result = subprocess.run(
            ["gh", *args], capture_output=True, text=True, timeout=30
        )
        if "API rate limit exceeded" in result.stderr:
            print("\nGitHub API rate limit exceeded; retrying in 60 seconds")
            time.sleep(60)
            result = subprocess.run(
                ["gh", *args], capture_output=True, text=True, timeout=30
            )
        if result.returncode == 0:
            return True, result.stdout.strip()
        errors = []
        for value in (result.stderr, result.stdout):
            value = value.strip()
            if value and value not in errors:
                errors.append(value)
        return False, "\n".join(errors) or f"gh exited with status {result.returncode}"
    except FileNotFoundError:
        return False, "gh CLI not found: https://cli.github.com"
    except subprocess.TimeoutExpired:
        return False, "gh command timed out after 30 seconds"


def should_exclude_line(line, path, code=None, repo=None):
    """Remove known non-actionable GitHub code-search matches."""
    path_lower = path.lower()
    repo_name = (repo or "").removeprefix("opensafely/").lower()
    filename = Path(path_lower).name
    if code == "R17" and repo_name == "openpregnosis":
        # OpenPregnosis uses R17 as an OPCS code, not an ICD-10 code.
        return True
    if Path(path_lower).suffix not in {".csv", ".py"}:
        return True
    if "ctv3" in line.lower() or "opcs" in path_lower:
        return True
    if (
        repo_name == "mh_pandemic"
        and filename == "ons-self-harm.csv"
        and code
        and code.startswith(("X67", "Y17"))
    ):
        # Both sets of changed descriptions remain within this broad self-harm list.
        return True
    if (
        repo_name == "postopcovid"
        and filename == "user-colincrooks-procedurecategory.csv"
        and code in {"W268", "W269"}
    ):
        # Both descriptions remain within this broad orthopaedic procedure category.
        return True
    if (
        repo_name == "surgery-research"
        and filename
        == "user-salmachaudhury-surgery-complication-icd-10-codes-veno-thromboembolic-disease.csv"
        and code == "I620"
    ):
        # The changed description remains within the codelist's intended definition.
        return True
    if code == "I620" and filename in {
        "opensafely-stroke-secondary-care.csv",
        "opensafely-cardiovascular-secondary-care.csv",
        "opensafely-icd-10-chapter-ix.csv",
        "uom-stroke-any-incl-history-icd10.csv",
        "uom-stroke-haemorrhagic-icd10.csv",
        "icd_stroke.csv",
    }:
        return True
    if (
        code
        and ("X67" in code or "Y17" in code)
        and filename
        in {
            "user-emilyherrett-self_harm_icd10.csv",
            "user-agleman-self-harm-and-suicide-icd-10.csv",
        }
    ):
        # Broad self harm codelist and all X67s are self harm even though description changed
        return True
    if (
        code
        and "X88" in code
        and filename
        in {
            "user-agleman-assault_violence-icd10.csv",
        }
    ):
        # Broad assault codelist and all X88s are assault even though description changed
        return True
    if (
        code
        and "X47" in code
        and filename
        in {
            "user-agleman-lifestyle-problems-icd10.csv",
        }
    ):
        # Acciental poisoning codes
        return True
    return "U12 small nuclear mutation" in line or any(
        re.match(pattern, line)
        for pattern in (
            r"^U\d\d\d,Unspecified diagnostic imaging",
            r"^K58\d,Percutaneous",
            r"^U10.*Falls",
            r"^K588,Other specified diagnostic transluminal operations",
        )
    )


def filter_github_search_results(all_results):
    filtered = {}
    for code, repo_results in all_results.items():
        kept_repos = {}
        for repo, matches in repo_results.items():
            kept = [
                match
                for match in matches
                if not should_exclude_line(
                    match["line_text"], match["path"], code, repo
                )
            ]
            if kept:
                kept_repos[repo] = kept
        filtered[code] = kept_repos
    return filtered


def search_code_in_org(code):
    """Search the opensafely GitHub organisation for one exact code."""
    print(f"  Searching for {code}...", end="", flush=True)
    results = defaultdict(list)
    seen_matches = set()
    for query in (
        f'"{code}" org:opensafely',
        f'"{code}" org:opensafely fork:true',
    ):
        success, output = run_gh_command(
            [
                "api",
                "--method",
                "GET",
                "--paginate",
                "--slurp",
                "-H",
                "Accept: application/vnd.github.text-match+json",
                "/search/code",
                "-f",
                f"q={query}",
                "-f",
                "per_page=100",
            ]
        )
        if not success:
            print(f" ERROR: {output}")
            return None
        try:
            response = json.loads(output) if output else []
        except json.JSONDecodeError as error:
            print(f" ERROR: invalid JSON: {error}")
            return None

        pages = response if isinstance(response, list) else [response]
        for page in pages:
            if "message" in page and "rate limit" in page["message"].lower():
                print(" RATE LIMITED")
                return None
            for item in page.get("items", []):
                path = item.get("path", "")
                repo = item.get("repository", {}).get("full_name", "")
                repo = repo.removeprefix("opensafely/")
                for text_match in item.get("text_matches", []):
                    for line in text_match.get("fragment", "").splitlines():
                        clean_line = line.strip()
                        match_key = (repo, path, clean_line)
                        if (
                            clean_line
                            and re.search(r"\b" + re.escape(code) + r"\b", line)
                            and not should_exclude_line(clean_line, path, code, repo)
                            and match_key not in seen_matches
                        ):
                            seen_matches.add(match_key)
                            results[repo].append(
                                {"path": path, "line_text": clean_line}
                            )
    total = sum(map(len, results.values()))
    message = (
        f" found in {len(results)} repo(s) ({total} matches)"
        if total
        else " (no results)"
    )
    print(message)
    return dict(results)


def find_all_codes_in_github(
    codes, force, input_paths: InputPaths = DEFAULT_INPUT_PATHS
):
    success, error = run_gh_command(["--version"])
    if not success:
        print(f"ERROR: Could not run gh CLI: {error}")
        sys.exit(1)
    cache = filter_github_search_results(
        {}
        if force
        else {
            code: value
            for code, value in load_cache(input_paths).items()
            if code in codes
        }
    )
    if cache:
        print(f"Loaded {len(cache)} cached results (use --force to refresh)\n")
    results = dict(cache)
    missing = codes - set(cache)
    for index, code in enumerate(sorted(missing)):
        found = search_code_in_org(code)
        if found is not None:
            results[code] = found
        if index < len(missing) - 1:
            time.sleep(2)
    if missing:
        results = filter_github_search_results(results)
        save_cache(results, input_paths)
    return filter_github_search_results(results)


def load_github_repo_file(repo, path):
    repo_name = repo.split("/")[-1]
    encoded_path = quote(path, safe="/")
    success, output = run_gh_command(
        ["api", f"repos/opensafely/{repo_name}/contents/{encoded_path}"]
    )
    if not success or not output:
        return None
    try:
        data = json.loads(output)
        if not data.get("content") and data.get("sha"):
            success, output = run_gh_command(
                ["api", f"repos/opensafely/{repo_name}/git/blobs/{data['sha']}"]
            )
            if not success or not output:
                return None
            data = json.loads(output)
        if data.get("encoding") != "base64" or not data.get("content"):
            return None
        return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
    except (json.JSONDecodeError, ValueError, TypeError):
        return None


def extract_icd10_codes(contents):
    return set(
        re.findall(
            r"(?<![A-Z0-9])[A-Z][0-9]{2}[A-Z0-9]*(?![A-Z0-9])",
            contents.upper(),
        )
    )


def get_actual_codes(group, codes):
    mappings = group.get("actual_codes_by_code", {})
    actual_codes = []
    for code in codes:
        for actual_code in mappings.get(code, group.get("actual_codes", [])):
            if actual_code not in actual_codes:
                actual_codes.append(actual_code)
    return actual_codes


def load_project_type_overrides(input_paths: InputPaths = DEFAULT_INPUT_PATHS):
    project_type_overrides_file = input_paths.file("project_type_overrides.json")
    if not project_type_overrides_file.exists():
        return {}
    try:
        with project_type_overrides_file.open() as f:
            overrides = json.load(f)
    except (OSError, json.JSONDecodeError) as error:
        print(
            f"WARNING: Could not load project type overrides: {error}", file=sys.stderr
        )
        return {}
    if not isinstance(overrides, dict):
        return {}
    valid_types = {"ehrql", "cohortextractor", "ignore"}
    return {
        repo.removeprefix("opensafely/"): project_type
        for repo, project_type in overrides.items()
        if isinstance(repo, str) and project_type in valid_types
    }


def get_project_type(repo, overrides=None):
    repo_name = repo.removeprefix("opensafely/")
    overrides = overrides or {}
    if repo_name in overrides:
        return overrides[repo_name]
    if repo in overrides:
        return overrides[repo]
    project_yaml = load_github_repo_file(repo, "project.yaml")
    if project_yaml is None:
        return None
    project_yaml = project_yaml.lower()
    if "ehrql" in project_yaml:
        return "ehrql"
    if "cohortextractor" in project_yaml:
        return "cohortextractor"
    return None


def filter_cohortextractor_moved_codes(all_results, groups, overrides=None):
    """Suppress CE findings already handled by a prefix in the same file."""
    group_by_code = {code: group for group in groups for code in group.get("codes", [])}
    repos = sorted(
        {repo for repo_results in all_results.values() for repo in repo_results}
    )
    print(f"Classifying {len(repos)} repositories...")
    project_types = {}
    for index, repo in enumerate(repos, start=1):
        print(f"  [{index}/{len(repos)}] {repo}...", end="", flush=True)
        project_types[repo] = get_project_type(repo, overrides)
        print(f" {project_types[repo] or 'unknown'}")
    file_cache = {}
    filtered = {}
    for code, repo_results in all_results.items():
        group = group_by_code.get(code)
        targets = [code, *get_actual_codes(group, [code])] if group else [code]
        kept_repos = {}
        for repo, matches in repo_results.items():
            if project_types.get(repo) == "ignore":
                continue
            kept = []
            for match in matches:
                covered = False
                if project_types.get(repo) == "cohortextractor" and group:
                    key = (repo, match["path"])
                    if key not in file_cache:
                        print(
                            f"  Checking prefix coverage in {repo}/{match['path']}...",
                            end="",
                            flush=True,
                        )
                        file_cache[key] = load_github_repo_file(*key)
                        print(" done")
                    file_codes = extract_icd10_codes(file_cache[key] or "")
                    covered = any(
                        len(prefix) >= 3
                        and all(target.startswith(prefix) for target in targets)
                        for prefix in file_codes
                    )
                if not covered:
                    kept.append(match)
            if kept:
                kept_repos[repo] = kept
        if kept_repos:
            filtered[code] = kept_repos
    return filtered, project_types


def load_prefix_matching_warnings(
    input_paths: InputPaths = DEFAULT_INPUT_PATHS,
):
    prefix_warnings_file = input_paths.file("prefix_matching_repos.csv")

    warnings = defaultdict(list)
    if not prefix_warnings_file.exists():
        print(f"INFO: {prefix_warnings_file} not found; skipping prefix warnings")
        return warnings
    try:
        with prefix_warnings_file.open() as f:
            for row in csv.DictReader(f):
                repo = row.get("repo", "").strip()
                if not repo or repo == "(not found in repos)":
                    continue
                warnings[repo.removeprefix("opensafely/")].append(
                    {
                        "codelist": row.get("codelist", "").strip(),
                        "current": row.get("current_event_count", "0").strip(),
                        "x_padded": row.get("event_count_with_x_padding", "0").strip(),
                        "with_prefix": row.get(
                            "event_count_with_prefix_matching", "0"
                        ).strip(),
                    }
                )
    except OSError as error:
        print(f"WARNING: Could not read prefix warnings: {error}")
    return warnings


def load_prefix_matching_details(
    input_paths: InputPaths = DEFAULT_INPUT_PATHS,
):
    prefix_details_file = input_paths.file("prefix_matching_details.json")

    if not prefix_details_file.exists():
        print(f"INFO: {prefix_details_file} not found; code details unavailable")
        return {}
    try:
        with prefix_details_file.open() as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as error:
        print(f"WARNING: Could not read prefix matching details: {error}")
        return {}


def load_swapped_codes(input_paths: InputPaths = DEFAULT_INPUT_PATHS):
    swapped_codes_file = input_paths.file("swapped_codes.json")
    try:
        with swapped_codes_file.open() as f:
            groups = json.load(f)
    except (OSError, json.JSONDecodeError) as error:
        print(f"ERROR loading moved codes: {error}")
        return {}, []
    codes = {
        code: group.get("description", "")
        for group in groups
        for code in group.get("codes", [])
    }
    print(f"Loaded {len(codes)} unique codes from {swapped_codes_file.name}\n")
    return codes, groups


def load_changed_code_definitions(input_paths: InputPaths = DEFAULT_INPUT_PATHS):
    changed_definitions_file = input_paths.file("changed_code_definitions.json")
    try:
        with changed_definitions_file.open() as f:
            entries = json.load(f)
    except (OSError, json.JSONDecodeError) as error:
        print(f"ERROR loading changed definitions: {error}")
        return {}
    changed = {}
    for entry in entries:
        code = entry.get("code", "").strip()
        definitions = entry.get("definitions", {})
        old = definitions.get("2016", "").strip()
        new = definitions.get("2019", "").strip()
        if code and old and new:
            changed[code] = {"2016": old, "2019": new}
    print(f"Loaded {len(changed)} codes with changed definitions\n")
    return changed
