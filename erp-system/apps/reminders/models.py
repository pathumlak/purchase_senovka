import calendar
from datetime import date, datetime, time

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


def add_one_month(d):
    """Return the same day-of-month one month later, clamped to the month length.

    e.g. 15 Jan -> 15 Feb, 31 Jan -> 28 Feb, 31 Dec -> 31 Jan (next year).
    """
    month = d.month + 1
    year = d.year
    if month > 12:
        month = 1
        year += 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(d.day, last_day))


class Reminder(models.Model):
    title = models.CharField(max_length=255)
    remind_date = models.DateField()
    remind_time = models.TimeField(null=True, blank=True)
    repeat_monthly = models.BooleanField(
        default=False,
        help_text='Repeat on the same date every month.',
    )
    is_done = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='reminders',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['remind_date', 'remind_time', 'id']

    def __str__(self):
        return f"{self.title} — {self.remind_date}"

    @property
    def remind_datetime(self):
        """Combine date + time; missing time is treated as end of day."""
        t = self.remind_time or time(23, 59)
        return timezone.make_aware(datetime.combine(self.remind_date, t))

    @property
    def is_past(self):
        return self.remind_datetime < timezone.localtime()

    @property
    def is_today(self):
        return self.remind_date == timezone.localdate()

    def roll_forward(self):
        """Advance a repeating reminder to its next future occurrence.

        Returns True if the date changed (caller should save).
        """
        if not self.repeat_monthly or self.is_done:
            return False
        changed = False
        # Advance month-by-month until the occurrence is in the future.
        while self.remind_datetime < timezone.localtime():
            self.remind_date = add_one_month(self.remind_date)
            changed = True
        return changed
