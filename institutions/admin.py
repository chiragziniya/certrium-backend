from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import (
    Institution,
    InstitutionDomain,
    InstitutionContact,
    InstitutionInvite,
    InstitutionRequest,
    InstitutionStaff,
    InstitutionDocument,
)


@admin.register(Institution)
class InstitutionAdmin(ModelAdmin):

    list_display = (
        "name",
        "email",
        "country",
        "status",
        "is_verified",
        "is_active",
        "created_at",
    )

    search_fields = (
        "name",
        "email",
        "country",
    )

    list_filter = (
        "status",
        "is_verified",
        "is_active",
        "country",
    )

    prepopulated_fields = {
        "slug": ("name",)
    }

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )


@admin.register(InstitutionDomain)
class InstitutionDomainAdmin(ModelAdmin):

    list_display = (
        "domain",
        "institution",
        "is_verified",
        "verified_at",
    )

    search_fields = (
        "domain",
        "institution__name",
    )

    list_filter = (
        "is_verified",
    )

    readonly_fields = (
        "verification_token",
        "verified_at",
        "created_at",
    )


@admin.register(InstitutionContact)
class InstitutionContactAdmin(ModelAdmin):

    list_display = (
        "name",
        "institution",
        "email",
        "contact_type",
        "is_primary",
    )

    search_fields = (
        "name",
        "email",
        "institution__name",
    )

    list_filter = (
        "contact_type",
        "is_primary",
    )


@admin.register(InstitutionInvite)
class InstitutionInviteAdmin(ModelAdmin):

    list_display = (
        "email",
        "institution",
        "status",
        "expires_at",
        "is_used",
        "created_at",
    )

    search_fields = (
        "email",
        "institution__name",
    )

    list_filter = (
        "status",
        "is_used",
    )

    readonly_fields = (
        "token",
        "accepted_at",
        "created_at",
    )

    ordering = (
        "-created_at",
    )


@admin.register(InstitutionRequest)
class InstitutionRequestAdmin(ModelAdmin):

    list_display = (
        "institution_name",
        "requested_by",
        "status",
        "converted_institution",
        "created_at",
    )

    search_fields = (
        "institution_name",
        "domain",
        "requested_by__email",
        "requested_email",
    )

    list_filter = (
        "status",
    )

    readonly_fields = (
        "reviewed_at",
        "contacted_at",
        "created_at",
        "updated_at",
    )


@admin.register(InstitutionStaff)
class InstitutionStaffAdmin(ModelAdmin):

    list_display = (
        "user",
        "institution",
        "role",
        "is_primary_contact",
        "is_active",
        "joined_at",
    )

    search_fields = (
        "user__email",
        "institution__name",
    )

    list_filter = (
        "role",
        "is_active",
        "is_primary_contact",
    )

    readonly_fields = (
        "joined_at",
        "created_at",
    )


@admin.register(InstitutionDocument)
class InstitutionDocumentAdmin(ModelAdmin):

    list_display = (
        "title",
        "institution",
        "document_type",
        "is_verified",
        "verified_at",
        "created_at",
    )

    search_fields = (
        "title",
        "institution__name",
    )

    list_filter = (
        "document_type",
        "is_verified",
    )

    readonly_fields = (
        "verified_at",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )