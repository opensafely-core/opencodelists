from django.shortcuts import get_object_or_404, render

from .models import Concept, HistorySubstitution


def concept(request, id):
    concept = get_object_or_404(
        Concept.objects.filter(pk=id).prefetch_related("descriptions")
    )

    ctx = {
        "concept": concept,
        "parents": concept.parents.order_by("fully_specified_name"),
        "children": concept.children.order_by("fully_specified_name"),
    }

    return render(request, "snomedct/concept.html", ctx)


def history_substitutions(request):
    old_codes = request.GET.get("old", "").split(",")
    new_codes = request.GET.get("new", "").split(",")

    if old_codes is None:
        if new_codes is None:
            substitutions = None
        else:
            substitutions = HistorySubstitution.objects.filter(
                new_concept__id__in=new_codes
            )
    else:
        if new_codes is None:
            substitutions = HistorySubstitution.objects.filter(
                old_concept__id__in=old_codes
            )
        else:
            substitutions = HistorySubstitution.objects.filter(
                old_concept__id__in=old_codes, new_concept__id__in=new_codes
            )

    if substitutions is not None:
        substitutions = substitutions.order_by("old_concept_fsn", "new_concept_fsn")

    ctx = {"substitutions": substitutions}
    return render(request, "snomedct/history_substitutions.html", ctx)
