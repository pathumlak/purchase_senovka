from django.utils import timezone

from .models import Reminder


def reminder_badge(request):
    """Expose the count of due (today or overdue) reminders for the topbar bell."""
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return {}
    today = timezone.localdate()
    due_count = Reminder.objects.filter(is_done=False, remind_date__lte=today).count()
    return {'reminders_due_count': due_count}
