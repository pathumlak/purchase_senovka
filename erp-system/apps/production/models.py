from django.db import models
from django.utils import timezone


class ProductCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Product Categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(
        ProductCategory, on_delete=models.CASCADE, related_name='products'
    )
    size = models.CharField(max_length=100, blank=True, null=True)
    qty = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text='Available quantity')
    supplier = models.ForeignKey(
        'suppliers.Supplier',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='products',
    )
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('name', 'category')

    def __str__(self):
        return f"{self.name} ({self.category.name})"


class Machine(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class DailyRunningMachine(models.Model):
    production_date = models.DateField(default=timezone.localdate, db_index=True)
    machine_name = models.CharField(max_length=255)
    machine_not_working = models.BooleanField(default=False)
    item = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='daily_machine_runs',
        null=True, blank=True,
    )
    machine_operator = models.CharField(max_length=255, blank=True)
    crusher_operator = models.CharField(max_length=255, blank=True)
    material_mixer = models.CharField(max_length=255, blank=True)
    extra_work_employee = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-production_date', '-id']
        verbose_name = 'Daily Running Machine'
        verbose_name_plural = 'Daily Running Machines'

    def __str__(self):
        item_label = self.item.name if self.item else 'Not Working'
        return f"{self.production_date} | {self.machine_name} | {item_label}"


class DailyWorkAssignment(models.Model):
    production_date = models.DateField(unique=True, db_index=True)
    crusher_operator = models.CharField(max_length=255, blank=True)
    material_mixer = models.CharField(max_length=255, blank=True)
    extra_work_employee = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-production_date']
        verbose_name = 'Daily Work Assignment'
        verbose_name_plural = 'Daily Work Assignments'

    def __str__(self):
        return f"Work Assignment {self.production_date}"


class ProductionEntry(models.Model):
    date = models.DateField(default=timezone.localdate, db_index=True)
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name='production_entries'
    )
    qty_added = models.DecimalField(max_digits=12, decimal_places=2)
    qty_before = models.DecimalField(max_digits=12, decimal_places=2)
    qty_after = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.TextField(blank=True, default='')
    created_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='production_entries'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Production Entry'
        verbose_name_plural = 'Production Entries'

    def __str__(self):
        return f"{self.date} | {self.product.name} | +{self.qty_added}"


# ── Shared Employee model ──────────────────────────────────────

class Employee(models.Model):
    name = models.CharField(max_length=255, unique=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Employees'

    def __str__(self):
        return self.name


# ── Shift Production Log (previous feature) ────────────────────

class ShiftProductionLog(models.Model):
    POINT_CHOICES = [(0, '0 – No Penalty'), (1, '1 – Penalty')]

    shift_start = models.DateTimeField(db_index=True)
    shift_end = models.DateTimeField()
    machine_no = models.CharField(max_length=255)
    item_name = models.CharField(max_length=255)
    cavity = models.PositiveIntegerField()
    cycle_time_seconds = models.PositiveIntegerField()
    target_qty = models.IntegerField()
    actual_qty = models.IntegerField()
    downtime_minutes = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    downtime_reason = models.TextField(blank=True, default='')
    point = models.IntegerField(choices=POINT_CHOICES, default=1)
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name='shift_logs')
    remarks = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-shift_start', '-id']
        verbose_name = 'Shift Production Log'
        verbose_name_plural = 'Shift Production Logs'

    @property
    def penalty_points(self):
        return self.point

    @property
    def auto_point(self):
        return 1 if self.actual_qty < self.target_qty else 0

    @property
    def shortfall(self):
        return max(0, self.target_qty - self.actual_qty)

    @staticmethod
    def calc_target(shift_start, shift_end, cycle_time_seconds, cavity):
        if not all([shift_start, shift_end, cycle_time_seconds, cavity]):
            return 0
        duration = (shift_end - shift_start).total_seconds()
        if duration <= 0 or cycle_time_seconds <= 0:
            return 0
        return int(duration / cycle_time_seconds) * cavity

    def __str__(self):
        return f"{self.shift_start.date()} | {self.machine_no} | {self.employee.name}"


# ── Target Calculation System ──────────────────────────────────

class ProductionItem(models.Model):
    name = models.CharField(max_length=255, unique=True)
    hourly_qty = models.DecimalField(max_digits=8, decimal_places=2, help_text='Target quantity per 1 hour')
    description = models.TextField(blank=True, default='')
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Production Item'
        verbose_name_plural = 'Production Items'

    def __str__(self):
        return f"{self.name} ({self.hourly_qty}/hr)"


class ShiftTemplate(models.Model):
    name = models.CharField(max_length=100, unique=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    crosses_midnight = models.BooleanField(default=False, help_text='End time is on the next day')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Shift Template'
        verbose_name_plural = 'Shift Templates'

    @property
    def duration_hours(self):
        from datetime import datetime as dt, timedelta
        base = dt(2000, 1, 1)
        s = dt.combine(base, self.start_time)
        e = dt.combine(base, self.end_time)
        if self.crosses_midnight:
            e += timedelta(days=1)
        return (e - s).total_seconds() / 3600

    @property
    def duration_display(self):
        h = self.duration_hours
        hrs = int(h)
        mins = int(round((h - hrs) * 60))
        return f"{hrs}h {mins}m" if mins else f"{hrs}h"

    def __str__(self):
        return f"{self.name} ({self.duration_display})"


class TargetLog(models.Model):
    POINT_CHOICES = [(0, '0 – Not Achieved'), (1, '1 – Achieved')]

    date = models.DateField(db_index=True)
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name='target_logs')
    machine_name = models.CharField(max_length=255)
    item = models.ForeignKey(ProductionItem, on_delete=models.PROTECT, related_name='target_logs')
    shift_template = models.ForeignKey(
        ShiftTemplate, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='target_logs',
    )
    cavity = models.PositiveIntegerField(default=1)
    cycle_time_seconds = models.PositiveIntegerField(null=True, blank=True)
    target_qty = models.IntegerField()
    actual_qty = models.IntegerField()
    downtime_minutes = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    downtime_reason = models.TextField(blank=True, default='')
    point = models.IntegerField(choices=POINT_CHOICES, default=1)
    remarks = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Target Log'
        verbose_name_plural = 'Target Logs'

    @staticmethod
    def calc_target(item, shift_template):
        if not item or not shift_template:
            return 0
        return int(float(item.hourly_qty) * shift_template.duration_hours)

    @property
    def auto_point(self):
        return 1 if self.actual_qty >= self.target_qty else 0

    def __str__(self):
        return f"{self.date} | {self.employee.name} | {self.item.name}"