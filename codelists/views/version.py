from django.contrib import messages
from django.shortcuts import render
from django.utils.html import format_html

from ..models import Status
from ..presenters import present_search_results
from .decorators import load_version


@load_version
def version(request, clv):
    child_map = None
    code_to_status = None
    code_to_term = None
    tree_tables = None
    if clv.coding_system_id in ["bnf", "ctv3", "icd10", "snomedct"]:
        coding_system = clv.coding_system

        hierarchy = clv.codeset.hierarchy
        child_map = {c: list(pp) for c, pp in hierarchy.child_map.items()}
        code_to_term = coding_system.code_to_term(hierarchy.nodes)
        included = set(clv.codes) & hierarchy.nodes
        excluded = hierarchy.nodes - included
        code_to_status = {
            **{code: "+" for code in included},
            **{code: "-" for code in excluded},
        }
        ancestor_codes = hierarchy.filter_to_ultimate_ancestors(included)
        unknown_codes = set(clv.codes) - set(coding_system.lookup_names(clv.codes))
        if unknown_codes:
            messages.warning(
                request,
                format_html(
                    f"WARNING: Codelist contains codes not found in {coding_system.name}"
                ),
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

    def build_tree_data():
        def process_node(code, depth=0):
            children = child_map.get(code, [])
            processed_children = [
                process_node(child_code, depth + 1) for child_code in children
            ]
            processed_children.sort(key=lambda x: x["name"])

            return {
                "id": code,
                "name": code_to_term[code],
                "status": code_to_status[code],
                "children": processed_children,
                "depth": depth,
            }

        def generate_output_data():
            return [
                {"title": title, "children": [process_node(code) for code in children]}
                for title, children in tree_tables
            ]

        return generate_output_data()

    ctx = {
        "clv": clv,
        "codelist": clv.codelist,
        "references": clv.codelist.references.all(),
        "signoffs": clv.codelist.signoffs.all(),
        "versions": visible_versions,
        "headers": headers,
        "rows": rows,
        "search_results": present_search_results(clv, code_to_term),
        "user_can_edit": user_can_edit,
        "can_create_new_version": can_create_new_version,
        "tree_data": build_tree_data(),
    }
    return render(request, "codelists/version.html", ctx)
