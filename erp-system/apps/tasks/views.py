from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from erp.decorators import superadmin_required
from erp.utils import log_activity
from .models import Task


def task_board(request):
    tasks = Task.objects.select_related('assigned_to', 'created_by').all()
    context = {
        'todo_tasks':        tasks.filter(status=Task.TODO),
        'inprogress_tasks':  tasks.filter(status=Task.IN_PROGRESS),
        'done_tasks':        tasks.filter(status=Task.DONE),
        'users':             User.objects.filter(is_active=True).order_by('username'),
        'total':             tasks.count(),
        'done_count':        tasks.filter(status=Task.DONE).count(),
        'inprogress_count':  tasks.filter(status=Task.IN_PROGRESS).count(),
        'todo_count':        tasks.filter(status=Task.TODO).count(),
    }
    return render(request, 'tasks/task_board.html', context)


@superadmin_required
def task_create(request):
    if request.method == 'POST':
        title       = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        priority    = request.POST.get('priority', Task.MEDIUM)
        due_date    = request.POST.get('due_date') or None
        assigned_to_id = request.POST.get('assigned_to') or None
        image       = request.FILES.get('image')

        if not title:
            messages.error(request, 'Title is required.')
            return redirect('task_board')

        task = Task(
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            created_by=request.user,
            image=image,
        )
        if assigned_to_id:
            task.assigned_to_id = int(assigned_to_id)
        task.save()

        log_activity(request, 'tasks', 'task_created',
                     f"Task created: {task.title}", reverse('task_board'), related_id=task.pk)
        messages.success(request, 'Task created successfully.')
    return redirect('task_board')


@superadmin_required
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        title       = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        priority    = request.POST.get('priority', Task.MEDIUM)
        due_date    = request.POST.get('due_date') or None
        assigned_to_id = request.POST.get('assigned_to') or None
        status      = request.POST.get('status', task.status)

        if not title:
            messages.error(request, 'Title is required.')
            return redirect('task_board')

        task.title       = title
        task.description = description
        task.priority    = priority
        task.due_date    = due_date
        task.status      = status
        task.assigned_to_id = int(assigned_to_id) if assigned_to_id else None

        if 'image' in request.FILES:
            task.image = request.FILES['image']
        elif request.POST.get('clear_image'):
            task.image = None

        task.save()
        log_activity(request, 'tasks', 'task_updated',
                     f"Task updated: {task.title}", reverse('task_board'))
        messages.success(request, 'Task updated successfully.')
    return redirect('task_board')


@superadmin_required
@require_POST
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    name = task.title
    task.delete()
    log_activity(request, 'tasks', 'task_deleted',
                 f"Task deleted: {name}", reverse('task_board'))
    messages.success(request, 'Task deleted.')
    return redirect('task_board')


@require_POST
def task_status_update(request, pk):
    task = get_object_or_404(Task, pk=pk)
    new_status = request.POST.get('status')
    if new_status not in (Task.TODO, Task.IN_PROGRESS, Task.DONE):
        return JsonResponse({'error': 'Invalid status'}, status=400)

    task.status = new_status
    task.save(update_fields=['status', 'updated_at'])

    log_activity(request, 'tasks', 'task_status_changed',
                 f"Task '{task.title}' moved to {task.get_status_display()}",
                 reverse('task_board'), related_id=task.pk)

    return JsonResponse({'ok': True, 'status': task.status, 'label': task.get_status_display()})
