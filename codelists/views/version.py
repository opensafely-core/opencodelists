from django.shortcuts import render

from ..coding_systems import CODING_SYSTEMS
from ..models import Status
from ..presenters import present_search_results
from .decorators import load_version


@load_version
def version(request, clv):
    child_map = None
    code_to_status = None
    code_to_term = None
    parent_map = None
    tree_tables = None
    if clv.coding_system_id in ["bnf", "ctv3", "icd10", "snomedct"]:
        coding_system = CODING_SYSTEMS[clv.coding_system_id]

        hierarchy = clv.codeset.hierarchy
        parent_map = {p: list(cc) for p, cc in hierarchy.parent_map.items()}
        child_map = {c: list(pp) for c, pp in hierarchy.child_map.items()}
        code_to_term = coding_system.code_to_term(hierarchy.nodes)
        code_to_status = {
            code: "+" if code in clv.codes else "-" for code in hierarchy.nodes
        }
        ancestor_codes = hierarchy.filter_to_ultimate_ancestors(
            set(clv.codes) & hierarchy.nodes
        )
        tree_tables = sorted(
            (type.title(), sorted(codes, key=code_to_term.__getitem__))
            for type, codes in coding_system.codes_by_type(
                ancestor_codes, hierarchy
            ).items()
        )

    headers, *rows = clv.table
    user_can_edit = clv.codelist.can_be_edited_by(request.user)
    visible_versions = clv.codelist.visible_versions(request.user)
    can_create_new_version = not clv.codelist.versions.filter(
        status=Status.DRAFT
    ).exists()

    ctx = {
        "clv": clv,
        "codelist": clv.codelist,
        "references": clv.codelist.references.all(),
        "signoffs": clv.codelist.signoffs.all(),
        "versions": visible_versions,
        "headers": headers,
        "rows": rows,
        "tree_tables": tree_tables,
        "parent_map": parent_map,
        "child_map": child_map,
        "code_to_term": code_to_term,
        "code_to_status": code_to_status,
        "search_results": present_search_results(clv, code_to_term),
        "user_can_edit": user_can_edit,
        "can_create_new_version": can_create_new_version,
    }
    return render(request, "codelists/version.html", ctx)
