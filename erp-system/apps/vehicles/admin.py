from django.contrib import admin
from .models import VehicleLog

@admin.register(VehicleLog)
class VehicleLogAdmin(admin.ModelAdmin):
    list_display = ('date', 'driver_name', 'from_location', 'to_location', 'total_km', 'purpose')
    list_filter  = ('date', 'driver_name')
    search_fields = ('driver_name', 'from_location', 'to_location', 'purpose')
