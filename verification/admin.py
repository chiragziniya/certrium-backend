from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import *


@admin.register(VerificationRecord)
class VerificationRecordAdmin(ModelAdmin):
    list_display = ("id", "status", "created_at")


@admin.register(CredentialDocument)
class CredentialDocumentAdmin(ModelAdmin):
    list_display = ("id", "created_at")


@admin.register(VerificationEvent)
class VerificationEventAdmin(ModelAdmin):
    list_display = ("id", "event_type", "created_at")


@admin.register(VerificationComment)
class VerificationCommentAdmin(ModelAdmin):
    list_display = ("id", "created_at")