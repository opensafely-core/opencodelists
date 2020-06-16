from django.shortcuts import get_object_or_404, render

from .forms import BrowserForm
from .models import STATED_RELATIONSHIP, Concept


def concept(request, id):
    concept = get_object_or_404(
        Concept.objects.filter(pk=id).prefetch_related("descriptions")
    )

    form = BrowserForm(request.GET)
    if form.is_valid():
        relationship_types = form.cleaned_data["relationship_types"]
    else:
        relationship_types = [STATED_RELATIONSHIP]

    buttons = []
    for choice in form.fields["relationship_types"]._choices:

        button = {"label": choice[1]}
        if choice[0] in relationship_types:
            updated_relationship_types = [
                t for t in relationship_types if t != choice[0]
            ]
            button["selected"] = True
        else:
            updated_relationship_types = relationship_types + [choice[0]]
            button["selected"] = False

        qd = request.GET.copy()
        qd.setlist("relationship_types", updated_relationship_types)
        button["href"] = "./?" + qd.urlencode()
        buttons.append(button)

    ctx = {
        "concept": concept,
        "parents": concept.parents(relationship_types).order_by("fully_specified_name"),
        "children": concept.children(relationship_types).order_by(
            "fully_specified_name"
        ),
        "buttons": buttons,
    }

    return render(request, "snomedct/concept.html", ctx)
