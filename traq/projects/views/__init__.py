from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.db import connection
from django.contrib import messages
from ..forms import ProjectForm
from ..models import Project, Milestone
from traq.permissions.decorators import can_do, can_view, can_edit, can_create
from traq.utils import querySetToJSON

@can_do()
def all(request):
    projects = []
    projects.append(Project.objects.filter(status=Project.ACTIVE))
    projects.append(Project.objects.filter(status=Project.INACTIVE))
    return render(request, 'projects/all.html', {
        'projects': projects,
    })

@can_view(Project)
def meta(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    try:
        target_completion = Milestone.objects.get(project=project, name="Target Completion Date").due_on
    except (Milestone.DoesNotExist, Milestone.MultipleObjectsReturned) as e:
        target_completion = None

    return render(request, 'projects/meta.html', {
        'project': project,
        'target_completion': target_completion,
    })

@can_view(Project)
def detail(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    tickets = project.tickets()
    components = project.components()
    work = project.latestWork(10)
    tickets_json = querySetToJSON(tickets)
    milestones = Milestone.objects.filter(project=project)

    return render(request, 'projects/detail.html', {
        'project': project,
        'tickets': tickets,
        'queries': connection.queries,
        'components': components,
        'work': work,
        'tickets_json': tickets_json,
        'milestones': milestones,
    })

@can_edit(Project)
def edit(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project, created_by=project.created_by)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("projects-all"))
    else:
        form = ProjectForm(instance=project, created_by=project.created_by)

    return render(request, 'projects/create.html', {
        'form': form,
    })

@can_create(Project)
def create(request):
    if request.method == "POST":
        form = ProjectForm(request.POST, created_by=request.user)
        if form.is_valid():
            form.save()
            form.instance.createDefaultComponents()
            return HttpResponseRedirect(reverse("projects-all"))
    else:
        form = ProjectForm(created_by=request.user)

    return render(request, 'projects/create.html', {
        'form': form,
    })
