from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import *


@admin.register(AuditLog)
class AuditLogAdmin(ModelAdmin):
    list_display = ("id", "created_at")


@admin.register(SecurityEvent)
class SecurityEventAdmin(ModelAdmin):
    list_display = ("id", "created_at")


@admin.register(ActivityTimeline)
class ActivityTimelineAdmin(ModelAdmin):
    list_display = ("id", "created_at")