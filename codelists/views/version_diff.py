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

    if lhs_coding_system.id == "dmd":
        lhs_codes = get_dmd_codes(clv)
        rhs_codes = get_dmd_codes(other_clv)
        if lhs_codes is None or rhs_codes is None:
            raise HttpResponseBadRequest("Could not identify code columns")
    else:
        lhs_codes = set(clv.codes)
        rhs_codes = set(other_clv.codes)

    lhs_only_codes = lhs_codes - rhs_codes
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
        "lhs_only_summary": summarise(lhs_only_codes, lhs_coding_system),
        "rhs_only_summary": summarise(rhs_only_codes, rhs_coding_system),
        "common_summary": summarise(common_codes, lhs_coding_system),
    }

    return render(request, "codelists/version_diff.html", ctx)


def summarise(codes, coding_system):
    code_to_term = coding_system.code_to_term(codes)

    if coding_system.id == "dmd":
        # dm+d has no hierarchy to look up, just return the codes themselves with their
        # terms
        summary = [
            {
                "code": code,
                "term": code_to_term[code],
            }
            for code in codes
        ]
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


def get_dmd_codes(clv):
    """
    Extract dm+d codes from a codelist version's csv_data
    """
    # Uploaded dm+d codelists have a variety of headers
    # All of these represent the code column in at least one codelist version
    possible_code_columns = ["dmd_id", "code", "id", "snomed_id", "dmd"]
    headers, *rows = clv.table

    def _get_col_ix():
        column = next(
            (col for col in possible_code_columns if col.strip() in headers), None
        )
        if column:
            return headers.index(column)

    code_ix = _get_col_ix()
    if code_ix is None:
        return
    return {row[code_ix] for row in rows}
