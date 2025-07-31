from django.core.exceptions import BadRequest
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import render

from opencodelists.hash_utils import unhash

from ..hierarchy import Hierarchy
from ..models import CodelistVersion
from .decorators import load_version


@load_version
def version_diff(request, clv, other_tag_or_hash):
    other_clv = None

    # 1. If other_tag_or_hash is a hash, try to find the CodelistVersion by ID
    try:
        id = unhash(other_tag_or_hash, "CodelistVersion")
        codelist_versions_matching_id = CodelistVersion.objects.filter(id=id)
        if codelist_versions_matching_id.count() == 1:
            other_clv = codelist_versions_matching_id.first()
    except ValueError:
        pass

    # 2. If no match, then probably a tag, so see if a unique tag matches
    if other_clv is None:
        codelist_versions_matching_tag = CodelistVersion.objects.filter(
            tag=other_tag_or_hash
        )
        if codelist_versions_matching_tag.count() == 1:
            other_clv = codelist_versions_matching_tag.first()

    # 3. If still no match, see if the tag matches a CodelistVersion for the LHS codelist
    #    so e.g. diffing pcd refsets like ./depr_cod/20210127/diff/20241205/ where every
    #    refset in an import has the same tag
    if other_clv is None:
        codelist_versions_matching_tag_in_codelist = CodelistVersion.objects.filter(
            tag=other_tag_or_hash, codelist=clv.codelist
        ).exclude(id=clv.id)
        if codelist_versions_matching_tag_in_codelist.count() == 1:
            other_clv = codelist_versions_matching_tag_in_codelist.first()

    if other_clv is None or clv.coding_system_id != other_clv.coding_system_id:
        raise Http404

    lhs_coding_system = clv.coding_system
    rhs_coding_system = other_clv.coding_system

    def _get_clv_codes(codelist_version):
        if codelist_version.csv_data:
            csv_data_codes_to_terms = get_csv_data_code_to_terms(codelist_version)
            if csv_data_codes_to_terms is None:
                raise BadRequest("Could not identify code columns")
            return set(csv_data_codes_to_terms), csv_data_codes_to_terms
        return set(codelist_version.codes), None

    try:
        lhs_codes, lhs_csv_data_codes_to_terms = _get_clv_codes(clv)
        rhs_codes, rhs_csv_data_codes_to_terms = _get_clv_codes(other_clv)
    except BadRequest as err:
        return HttpResponseBadRequest(str(err))

    lhs_only_codes = set(lhs_codes) - set(rhs_codes)
    rhs_only_codes = rhs_codes - lhs_codes
    common_codes = lhs_codes & rhs_codes

    ctx = {
        "lhs": clv,
        "rhs": other_clv,
        "lhs_codes": lhs_codes,
        "rhs_codes": rhs_codes,
        "lhs_only_codes": lhs_only_codes,
        "rhs_only_codes": rhs_only_codes,
        "common_codes": common_codes,
        "lhs_only_summary": summarise(
            lhs_only_codes, lhs_coding_system, lhs_csv_data_codes_to_terms
        ),
        "rhs_only_summary": summarise(
            rhs_only_codes, rhs_coding_system, rhs_csv_data_codes_to_terms
        ),
        "common_summary": summarise(
            common_codes, lhs_coding_system, lhs_csv_data_codes_to_terms
        ),
    }

    return render(request, "codelists/version_diff.html", ctx)


def summarise(codes, coding_system, csv_data_codes_to_terms=None):
    csv_data_codes_to_terms = csv_data_codes_to_terms or {}
    code_to_term = coding_system.code_to_term(codes)

    def get_term(code):
        term = code_to_term[code]
        if term == "Unknown" and csv_data_codes_to_terms.get(code) is not None:
            term = f"[Unknown] {csv_data_codes_to_terms[code]}"
        return term

    if not coding_system.is_builder_compatible():
        # if the coding system has no hierarchy to look up, just return the codes
        # themselves with their terms
        summary = [{"code": code, "term": get_term(code)} for code in codes]
    else:
        summary = []
        hierarchy = Hierarchy.from_codes(coding_system, codes)
        ancestor_codes = hierarchy.filter_to_ultimate_ancestors(codes)

        for ancestor_code in ancestor_codes:
            descendants = sorted(
                (
                    {"code": code, "term": get_term(code)}
                    for code in (
                        hierarchy.descendants(ancestor_code) & codes - {ancestor_code}
                    )
                ),
                key=lambda d: d["term"],
            )
            summary.append(
                {
                    "code": ancestor_code,
                    "term": get_term(ancestor_code),
                    "descendants": descendants,
                }
            )
    summary.sort(key=lambda d: d["term"])
    return summary


def get_csv_data_code_to_terms(clv):
    if not clv.csv_data:
        return

    # Old style codelists (i.e. those created with CSV data via the version_create view
    # /codelist/<org or user>/add/) are now required to contain a column named "code"
    # or "dmd_id".
    # However, older ones could be uploaded with any column names, so we need to
    # check the headers to identify the most likely one
    # These represent the valid case-insensitive code column names across all existing
    # old-style codelists
    possible_columns_by_coding_system = {
        "dmd": {
            "code": ["code", "dmd_id", "id", "snomed_id", "dmd"],
            "term": ["term", "name", "dmd_name", "nm"],
            "type": ["dmd_type", "obj_type", "type"],
        },
        "snomedct": {
            "code": ["code", "id", "snomed_id", "snomedcode", "dmd_id"],
            "term": ["term", "name", "dmd_name"],
        },
        "icd10": {
            "code": ["code", "id", "icd code", "icd_code", "icd", "icd10_code"],
            "term": ["term", "description", "diag_desc"],
        },
        "ctv3": {
            "code": ["code", "ctv3id", "ctv3code", "ctv3_id"],
            "term": [
                "term",
                "ctv3preferredtermdesc",
                "ctv3_description",
                "ctv3_description",
                "ctvterm",
                "readterm",
                "ctvterm",
            ],
        },
    }

    headers, *rows = clv.table
    headers = [header.lower().strip() for header in headers]
    possible_columns = possible_columns_by_coding_system.get(
        clv.codelist.coding_system_id, {"code": ["code"], "term": ["term"]}
    )

    def _get_col_ix(col_type):
        column = next(
            (col for col in possible_columns.get(col_type, []) if col in headers), None
        )
        if column:
            return headers.index(column)

    code_ix = _get_col_ix("code")
    if code_ix is None:
        return
    term_ix = _get_col_ix("term")
    type_ix = _get_col_ix("type")

    def get_term(row):
        if term_ix is None:
            return
        term = row[term_ix]
        if type_ix is not None:
            term = f"{term} ({row[type_ix]})"
        return term

    return {row[code_ix]: get_term(row) for row in rows}
