from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    SUPERADMIN = 'superadmin'
    ADMIN = 'admin'
    ROLE_CHOICES = [
        (SUPERADMIN, 'Super Admin'),
        (ADMIN, 'Admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ADMIN)

    def is_superadmin(self):
        return self.role == self.SUPERADMIN

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


class CompanySettings(models.Model):
    """Singleton — always use CompanySettings.get()."""
    company_name = models.CharField(max_length=200, default='Senovka Plastics')
    tagline      = models.CharField(max_length=300, blank=True)
    address      = models.TextField(blank=True)
    phone1       = models.CharField(max_length=30, blank=True, verbose_name='Phone 1')
    phone2       = models.CharField(max_length=30, blank=True, verbose_name='Phone 2')
    email        = models.EmailField(blank=True)
    website      = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = 'Company Settings'

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return self.company_name


class ActivityLog(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='activity_logs'
    )
    category = models.CharField(max_length=50)
    action = models.CharField(max_length=100)
    description = models.TextField()
    url = models.CharField(max_length=500, blank=True)
    related_id = models.IntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} - {self.action} ({self.category})"
