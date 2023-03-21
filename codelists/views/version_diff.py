from django.db.models import Q
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render

from opencodelists.hash_utils import unhash

from ..hierarchy import Hierarchy
from ..models import CodelistVersion
from .decorators import load_version


@load_version
def version_diff(request, clv, other_tag_or_hash):
    q = Q(tag=other_tag_or_hash)
    try:
        id = unhash(other_tag_or_hash, "CodelistVersion")
    except ValueError:
        pass
    else:
        q |= Q(id=id)

    other_clv = get_object_or_404(CodelistVersion.objects.filter(q))

    if clv.coding_system_id != other_clv.coding_system_id:
        raise Http404

    lhs_coding_system = clv.coding_system
    rhs_coding_system = other_clv.coding_system

    lhs_csv_data_codes_to_terms = rhs_csv_data_codes_to_terms = None
    if lhs_coding_system.id == "dmd":
        lhs_csv_data_codes_to_terms = get_dmd_codes_and_terms(clv)
        rhs_csv_data_codes_to_terms = get_dmd_codes_and_terms(other_clv)
        if lhs_csv_data_codes_to_terms is None or rhs_csv_data_codes_to_terms is None:
            return HttpResponseBadRequest("Could not identify code columns")
        lhs_codes = set(lhs_csv_data_codes_to_terms)
        rhs_codes = set(rhs_csv_data_codes_to_terms)
    else:
        lhs_codes = set(clv.codes)
        rhs_codes = set(other_clv.codes)

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
    code_to_term = coding_system.code_to_term(codes)

    if coding_system.id == "dmd":
        # dm+d has no hierarchy to look up, just return the codes themselves with their
        # terms
        summary = []
        for code in codes:
            term = code_to_term[code]
            if (
                term == "Unknown"
                and csv_data_codes_to_terms is not None
                and csv_data_codes_to_terms[code] is not None
            ):
                term = f"[Unknown] {csv_data_codes_to_terms[code]}"
            summary.append({"code": code, "term": term})
    else:
        summary = []
        hierarchy = Hierarchy.from_codes(coding_system, codes)
        ancestor_codes = hierarchy.filter_to_ultimate_ancestors(codes)

        for ancestor_code in ancestor_codes:
            descendants = sorted(
                (
                    {"code": code, "term": code_to_term[code]}
                    for code in (
                        hierarchy.descendants(ancestor_code) & codes - {ancestor_code}
                    )
                ),
                key=lambda d: d["term"],
            )
            summary.append(
                {
                    "code": ancestor_code,
                    "term": code_to_term[ancestor_code],
                    "descendants": descendants,
                }
            )
    summary.sort(key=lambda d: d["term"])
    return summary


def get_dmd_codes_and_terms(clv):
    """
    Extract dm+d codes from a codelist version's csv_data
    """
    # Uploaded dm+d codelists have a variety of headers
    # All of these represent the code column in at least one codelist version
    possible_columns = {
        "code": ["dmd_id", "code", "id", "snomed_id", "dmd"],
        "term": ["term", "name", "dmd_name", "nm"],
        "type": ["dmd_type", "obj_type", "type"],
    }
    headers, *rows = clv.table

    def _get_col_ix(col_type):
        column = next(
            (col for col in possible_columns[col_type] if col.strip() in headers), None
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
