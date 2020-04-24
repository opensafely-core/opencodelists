from django.shortcuts import get_object_or_404, render

from .models import Project


def project(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    ctx = {"project": project}
    return render(request, "opencodelists/project.html", ctx)
