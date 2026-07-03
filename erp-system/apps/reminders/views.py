from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from erp.utils import log_activity
from .models import Reminder, add_one_month


def _roll_repeating(queryset):
    """Advance any past-due repeating reminders to their next occurrence."""
    for reminder in queryset:
        if reminder.roll_forward():
            reminder.save(update_fields=['remind_date', 'updated_at'])


def reminder_list(request):
    # Keep recurring reminders pointing at their next upcoming occurrence.
    _roll_repeating(Reminder.objects.filter(repeat_monthly=True, is_done=False))

    active = Reminder.objects.filter(is_done=False)
    done = Reminder.objects.filter(is_done=True)[:50]
    today = timezone.localdate()

    context = {
        'overdue':  [r for r in active if r.remind_date < today],
        'todays':   [r for r in active if r.remind_date == today],
        'upcoming': [r for r in active if r.remind_date > today],
        'done':     done,
        'active_count': active.count(),
        'today': today,
    }
    return render(request, 'reminders/reminder_list.html', context)


def reminder_create(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        remind_date = request.POST.get('remind_date') or None
        remind_time = request.POST.get('remind_time') or None
        repeat_monthly = request.POST.get('repeat_monthly') == 'on'

        if not title or not remind_date:
            messages.error(request, 'A description and a date are required.')
            return redirect('reminder_list')

        reminder = Reminder.objects.create(
            title=title,
            remind_date=remind_date,
            remind_time=remind_time,
            repeat_monthly=repeat_monthly,
            created_by=request.user,
        )
        log_activity(request, 'reminders', 'reminder_created',
                     f"Reminder created: {reminder.title}",
                     reverse('reminder_list'), related_id=reminder.pk)
        messages.success(request, 'Reminder added.')
    return redirect('reminder_list')


def reminder_edit(request, pk):
    reminder = get_object_or_404(Reminder, pk=pk)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        remind_date = request.POST.get('remind_date') or None
        remind_time = request.POST.get('remind_time') or None
        repeat_monthly = request.POST.get('repeat_monthly') == 'on'

        if not title or not remind_date:
            messages.error(request, 'A description and a date are required.')
            return redirect('reminder_list')

        reminder.title = title
        reminder.remind_date = remind_date
        reminder.remind_time = remind_time
        reminder.repeat_monthly = repeat_monthly
        reminder.save()
        log_activity(request, 'reminders', 'reminder_updated',
                     f"Reminder updated: {reminder.title}", reverse('reminder_list'))
        messages.success(request, 'Reminder updated.')
    return redirect('reminder_list')


@require_POST
def reminder_delete(request, pk):
    reminder = get_object_or_404(Reminder, pk=pk)
    name = reminder.title
    reminder.delete()
    log_activity(request, 'reminders', 'reminder_deleted',
                 f"Reminder deleted: {name}", reverse('reminder_list'))
    messages.success(request, 'Reminder deleted.')
    return redirect('reminder_list')


@require_POST
def reminder_done(request, pk):
    reminder = get_object_or_404(Reminder, pk=pk)
    if reminder.repeat_monthly:
        # A recurring reminder is never "finished" — roll it to next month.
        reminder.remind_date = add_one_month(reminder.remind_date)
        reminder.roll_forward()
        reminder.save(update_fields=['remind_date', 'updated_at'])
        messages.success(request, f'"{reminder.title}" moved to {reminder.remind_date:%d %b %Y}.')
    else:
        reminder.is_done = True
        reminder.save(update_fields=['is_done', 'updated_at'])
        messages.success(request, f'"{reminder.title}" marked done.')
    log_activity(request, 'reminders', 'reminder_done',
                 f"Reminder completed: {reminder.title}", reverse('reminder_list'))
    return redirect('reminder_list')
