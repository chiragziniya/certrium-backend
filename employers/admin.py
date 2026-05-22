from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import (
    Employer,
    EmployerUser,
    EmployerVerificationAccess,
    EmployerVerificationReport,
)


@admin.register(Employer)
class EmployerAdmin(ModelAdmin):

    list_display = (
        "company_name",
        "email",
        "country",
        "status",
        "is_verified",
        "created_at",
    )

    search_fields = (
        "company_name",
        "email",
    )

    list_filter = (
        "status",
        "is_verified",
        "country",
    )

    prepopulated_fields = {
        "slug": ("company_name",)
    }


@admin.register(EmployerUser)
class EmployerUserAdmin(ModelAdmin):

    list_display = (
        "user",
        "employer",
        "role",
        "is_active",
        "joined_at",
    )

    list_filter = (
        "role",
        "is_active",
    )

    search_fields = (
        "user__email",
        "employer__company_name",
    )


@admin.register(EmployerVerificationAccess)
class EmployerVerificationAccessAdmin(ModelAdmin):

    list_display = (
        "employer",
        "candidate",
        "status",
        "approved_by_candidate",
        "expires_at",
    )

    list_filter = (
        "status",
        "approved_by_candidate",
    )

    search_fields = (
        "employer__company_name",
        "candidate__email",
    )


@admin.register(EmployerVerificationReport)
class EmployerVerificationReportAdmin(ModelAdmin):

    list_display = (
        "report_name",
        "employer",
        "candidate",
        "generated_at",
    )

    search_fields = (
        "report_name",
        "candidate__email",
        "employer__company_name",
    )