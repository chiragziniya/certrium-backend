from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import *


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(ModelAdmin):
    list_display = ("id", "created_at")


@admin.register(Invoice)
class InvoiceAdmin(ModelAdmin):
    list_display = ("id", "created_at")


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(ModelAdmin):
    list_display = ("id", "created_at")


@admin.register(UserSubscription)
class UserSubscriptionAdmin(ModelAdmin):
    list_display = ("id", "created_at")