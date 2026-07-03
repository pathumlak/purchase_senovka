from django.contrib import admin

from .models import Reminder


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ('title', 'remind_date', 'remind_time', 'repeat_monthly', 'is_done', 'created_by')
    list_filter = ('repeat_monthly', 'is_done', 'remind_date')
    search_fields = ('title',)
