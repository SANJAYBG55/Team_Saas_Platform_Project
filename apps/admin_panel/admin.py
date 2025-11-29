from django.contrib import admin
from .models import AdminDashboardWidget, AdminReport


@admin.register(AdminDashboardWidget)
class AdminDashboardWidgetAdmin(admin.ModelAdmin):
    list_display = ['title', 'widget_type', 'position', 'is_visible']
    list_filter = ['widget_type', 'is_visible']
    search_fields = ['title', 'description']


@admin.register(AdminReport)
class AdminReportAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'created_by', 'is_scheduled', 'created_at']
    list_filter = ['report_type', 'is_scheduled', 'schedule_frequency']
    search_fields = ['name', 'description']
