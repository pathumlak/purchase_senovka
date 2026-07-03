from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Task(models.Model):
    TODO        = 'todo'
    IN_PROGRESS = 'in_progress'
    DONE        = 'done'
    STATUS_CHOICES = [
        (TODO,        'To Do'),
        (IN_PROGRESS, 'In Progress'),
        (DONE,        'Done'),
    ]

    LOW    = 'low'
    MEDIUM = 'medium'
    HIGH   = 'high'
    PRIORITY_CHOICES = [
        (LOW,    'Low'),
        (MEDIUM, 'Medium'),
        (HIGH,   'High'),
    ]

    title       = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default=TODO, db_index=True)
    priority    = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default=MEDIUM)
    assigned_to = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_tasks')
    created_by  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    due_date    = models.DateField(null=True, blank=True)
    image       = models.ImageField(upload_to='tasks/', null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def is_overdue(self):
        return self.due_date and self.due_date < timezone.localdate() and self.status != self.DONE
