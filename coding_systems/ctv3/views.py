from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import Concept, Term


def index(request):
    if "q" in request.GET:
        q = request.GET["q"]
        if Concept.objects.filter(read_code=q).exists():
            return redirect(reverse("ctv3:concept", args=[q]))

        concepts = (
            Concept.objects.filter(
                Q(terms__name_1__icontains=q)
                | Q(terms__name_2__icontains=q)
                | Q(terms__name_3__icontains=q)
            )
            .prefetch_related("terms")
            .distinct()
        )

    else:
        q = None
        concepts = None

    ctx = {"q": q, "concepts": concepts}
    return render(request, "ctv3/index.html", ctx)


def concept(request, read_code):
    concept = get_object_or_404(
        Concept.objects.prefetch_related("terms"), read_code=read_code
    )
    ctx = {
        "concept": concept,
        "parents": sorted(
            concept.parents.prefetch_related("terms"), key=lambda c: c.preferred_term()
        ),
        "children": sorted(
            concept.children.prefetch_related("terms"), key=lambda c: c.preferred_term()
        ),
    }
    return render(request, "ctv3/concept.html", ctx)


def term(request, term_id):
    term = get_object_or_404(Term, term_id=term_id)
    ctx = {"term": term, "concepts": term.concepts.all()}
    return render(request, "ctv3/term.html", ctx)
