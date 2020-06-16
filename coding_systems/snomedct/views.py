from django.shortcuts import get_object_or_404, render

from .models import Concept


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
