from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib import admin

from unfold.admin import ModelAdmin
from unfold.forms import (
    AdminPasswordChangeForm,
    UserChangeForm,
    UserCreationForm,
)

from .models import User


# =========================================================
# UNREGISTER DEFAULT GROUP
# =========================================================

admin.site.unregister(Group)


# =========================================================
# CUSTOM USER ADMIN
# =========================================================

@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):

    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    ordering = ("-created_at",)

    list_display = (
        "email",
        "role",
        "institution",
        "is_active",
        "is_staff",
        "created_at",
    )

    list_filter = (
        "role",
        "is_active",
        "is_staff",
        "is_superuser",
        "institution",
    )

    search_fields = (
        "email",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    fieldsets = (

        (
            "Authentication",
            {
                "fields": (
                    "email",
                    "password",
                )
            },
        ),

        (
            "Profile",
            {
                "fields": (
                    "id",
                    "role",
                    "institution",
                    "is_email_verified",
                )
            },
        ),

        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),

        (
            "Important Dates",
            {
                "fields": (
                    "last_login",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "role",
                    "institution",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )

    filter_horizontal = (
        "groups",
        "user_permissions",
    )


# =========================================================
# GROUP ADMIN
# =========================================================

@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass