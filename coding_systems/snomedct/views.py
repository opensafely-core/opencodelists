import networkx as nx
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from .forms import BrowserForm
from .isa_hierarchy import load_hierarchy
from .models import ROOT_CONCEPT, STATED_RELATIONSHIP, Concept


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
        "children": concept.children(relationship_types).order_by("fully_specified_name"),
        "buttons": buttons,
    }

    return render(request, "snomedct/concept.html", ctx)


def concept_paths(request, id):
    hierarchy = load_hierarchy()
    try:
        concept = hierarchy.nodes[id]["concept"]
    except KeyError:
        raise Http404

    subgraph = hierarchy.subgraph(
        {id} | nx.ancestors(hierarchy, id) | nx.descendants(hierarchy, id)
    )

    # For reasons that I don't fully understand (it's something to do with the
    # graph having a single root and lots of leaves) it's very quick to use
    # networkx find all paths from the root to this node...
    ancestor_paths = [
        [subgraph.nodes[c]["concept"] for c in path]
        for path in nx.all_simple_paths(subgraph, ROOT_CONCEPT, id)
    ]
    ancestor_paths.sort(key=lambda path: [c.fully_specified_name for c in path])

    # ...but very very slow to use networkx to find all paths from this node to
    # the leaves.
    todo = [[id]]
    descendant_code_paths = []

    while todo:
        path = todo.pop()
        succs = subgraph.succ[path[-1]]
        if succs:
            for code1 in succs:
                todo.append(path + [code1])
        else:
            descendant_code_paths.append(path)

    descendant_paths = [
        [hierarchy.nodes[id]["concept"] for id in path]
        for path in descendant_code_paths
    ]
    descendant_paths.sort(key=lambda path: [c.fully_specified_name for c in path])

    ctx = {
        "concept": concept,
        "ancestor_paths": ancestor_paths,
        "descendant_paths": descendant_paths,
    }
    return render(request, "snomedct/concept-paths.html", ctx)
