from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import *


@admin.register(Wallet)
class WalletAdmin(ModelAdmin):
    list_display = ("id", "created_at")


@admin.register(WalletRecord)
class WalletRecordAdmin(ModelAdmin):
    list_display = ("id", "created_at")


@admin.register(WalletShare)
class WalletShareAdmin(ModelAdmin):
    list_display = ("id", "created_at")


@admin.register(WalletAccessLog)
class WalletAccessLogAdmin(ModelAdmin):
    list_display = ("id", "created_at")