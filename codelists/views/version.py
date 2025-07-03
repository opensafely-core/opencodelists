from django.contrib import messages
from django.shortcuts import render
from django.utils.html import format_html

from ..models import Status
from ..presenters import present_search_results
from ..similarity_service import find_similar_codelists
from ..tree_data import build_tree_data
from .decorators import load_version


@load_version
def version(request, clv):
    child_map = None
    code_to_status = None
    code_to_term = None
    tree_tables = None
    tree_data = None
    if clv.coding_system.is_builder_compatible():
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
        tree_data = build_tree_data(
            child_map,
            code_to_term,
            code_to_status,
            tree_tables,
            coding_system.sort_by_term,
        )

    headers, *rows = clv.table
    user_can_edit = clv.codelist.can_be_edited_by(request.user)
    visible_versions = clv.codelist.visible_versions(request.user)
    can_create_new_version = not clv.codelist.versions.filter(
        status=Status.DRAFT
    ).exists()

    # Find similar codelists
    similar_codelists = []
    similarity_matrix = []
    try:
        similar_results = find_similar_codelists(clv, threshold=0.1, max_results=10)
        # Convert similarity to percentage for display and add diff URL
        similar_codelists = [
            {
                "version": clv_similar,
                "similarity": similarity * 100,
                "diff_url": clv.get_diff_url(clv_similar),
            }
            for clv_similar, similarity in similar_results
        ]

        # Compute similarity matrix for all similar codelists (including current)
        if similar_codelists:
            from ..similarity import compute_exact_jaccard

            all_versions = [clv] + [item["version"] for item in similar_codelists]
            all_codes = [set(v.codes or []) for v in all_versions]

            # Build matrix with similarity percentages
            matrix_size = len(all_versions)
            similarity_matrix = []
            for i in range(matrix_size):
                row = []
                for j in range(matrix_size):
                    if i == j:
                        similarity = 100.0  # Self-similarity
                    else:
                        similarity = (
                            compute_exact_jaccard(all_codes[i], all_codes[j]) * 100
                        )
                    row.append(
                        {
                            "similarity": similarity,
                            "version_i": all_versions[i],
                            "version_j": all_versions[j],
                        }
                    )
                similarity_matrix.append(row)
    except Exception:
        # If similarity computation fails, show empty list
        pass

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
        "tree_data": tree_data,
        "similar_codelists": similar_codelists,
        "similarity_matrix": similarity_matrix,
    }
    return render(request, "codelists/version.html", ctx)
