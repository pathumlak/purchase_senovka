from decimal import Decimal
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class VehicleLog(models.Model):
    date          = models.DateField(default=timezone.localdate, db_index=True)
    driver_name   = models.CharField(max_length=100)
    from_location = models.CharField(max_length=200)
    to_location   = models.CharField(max_length=200)
    start_km      = models.DecimalField(max_digits=10, decimal_places=1)
    end_km        = models.DecimalField(max_digits=10, decimal_places=1)
    total_km      = models.DecimalField(max_digits=10, decimal_places=1, default=0)
    purpose       = models.CharField(max_length=500)
    created_at    = models.DateTimeField(auto_now_add=True)
    created_by    = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='vehicle_logs'
    )

    class Meta:
        ordering = ['-date', '-id']
        verbose_name = 'Vehicle Log'
        verbose_name_plural = 'Vehicle Logs'

    def save(self, *args, **kwargs):
        self.total_km = max(Decimal('0'), self.end_km - self.start_km)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.date} | {self.driver_name} | {self.total_km} km"
