from django.conf import settings
from django.db import models

from common.models import BaseModel


class AuditLog(BaseModel):

    class ActionType(models.TextChoices):
        CREATE = "CREATE", "Create"
        UPDATE = "UPDATE", "Update"
        DELETE = "DELETE", "Delete"

        LOGIN = "LOGIN", "Login"
        LOGOUT = "LOGOUT", "Logout"
        PASSWORD_CHANGE = "PASSWORD_CHANGE", "Password Change"

        VERIFICATION_CREATED = "VERIFICATION_CREATED", "Verification Created"
        VERIFICATION_UPDATED = "VERIFICATION_UPDATED", "Verification Updated"
        VERIFICATION_APPROVED = "VERIFICATION_APPROVED", "Verification Approved"
        VERIFICATION_REJECTED = "VERIFICATION_REJECTED", "Verification Rejected"
        VERIFICATION_REVOKED = "VERIFICATION_REVOKED", "Verification Revoked"

        DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED", "Document Uploaded"

        WALLET_SHARED = "WALLET_SHARED", "Wallet Shared"
        WALLET_ACCESS_GRANTED = "WALLET_ACCESS_GRANTED", "Wallet Access Granted"
        WALLET_ACCESS_REVOKED = "WALLET_ACCESS_REVOKED", "Wallet Access Revoked"

        EMPLOYER_ACCESS = "EMPLOYER_ACCESS", "Employer Access"

        INSTITUTION_CREATED = "INSTITUTION_CREATED", "Institution Created"
        INSTITUTION_UPDATED = "INSTITUTION_UPDATED", "Institution Updated"
        INSTITUTION_APPROVED = "INSTITUTION_APPROVED", "Institution Approved"

        USER_CREATED = "USER_CREATED", "User Created"
        USER_UPDATED = "USER_UPDATED", "User Updated"
        ROLE_CHANGED = "ROLE_CHANGED", "Role Changed"

        PERMISSION_GRANTED = "PERMISSION_GRANTED", "Permission Granted"
        PERMISSION_REVOKED = "PERMISSION_REVOKED", "Permission Revoked"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs"
    )

    action_type = models.CharField(
        max_length=50,
        choices=ActionType.choices,
        db_index=True
    )

    target_model = models.CharField(
        max_length=255
    )

    target_id = models.CharField(
        max_length=255
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True
    )

    user_agent = models.TextField(
        blank=True,
        null=True
    )

    request_method = models.CharField(
        max_length=10,
        blank=True,
        null=True
    )

    endpoint = models.CharField(
        max_length=500,
        blank=True,
        null=True
    )

    metadata = models.JSONField(
        default=dict,
        blank=True
    )

    old_values = models.JSONField(
        default=dict,
        blank=True
    )

    new_values = models.JSONField(
        default=dict,
        blank=True
    )

    is_sensitive = models.BooleanField(
        default=False
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        indexes = [
            models.Index(fields=["action_type", "created_at"]),
            models.Index(fields=["actor", "created_at"]),
            models.Index(fields=["target_model", "target_id"]),
        ]

    def __str__(self):
        return f"{self.action_type} - {self.target_model}"


class SecurityEvent(BaseModel):

    class EventType(models.TextChoices):
        LOGIN_SUCCESS = "LOGIN_SUCCESS", "Login Success"
        LOGIN_FAILED = "LOGIN_FAILED", "Login Failed"
        MFA_SUCCESS = "MFA_SUCCESS", "MFA Success"
        MFA_FAILED = "MFA_FAILED", "MFA Failed"
        PASSWORD_RESET = "PASSWORD_RESET", "Password Reset"

        SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY", "Suspicious Activity"
        RATE_LIMIT_TRIGGERED = "RATE_LIMIT_TRIGGERED", "Rate Limit Triggered"
        PERMISSION_DENIED = "PERMISSION_DENIED", "Permission Denied"

        TOKEN_REVOKED = "TOKEN_REVOKED", "Token Revoked"
        SESSION_EXPIRED = "SESSION_EXPIRED", "Session Expired"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="security_events"
    )

    event_type = models.CharField(
        max_length=50,
        choices=EventType.choices,
        db_index=True
    )

    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True
    )

    user_agent = models.TextField(
        blank=True,
        null=True
    )

    location = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    was_successful = models.BooleanField(
        default=True
    )

    details = models.JSONField(
        default=dict,
        blank=True
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Security Event"
        verbose_name_plural = "Security Events"
        indexes = [
            models.Index(fields=["user", "event_type"]),
            models.Index(fields=["event_type", "created_at"]),
        ]

    def __str__(self):
        return f"{self.event_type}"


class ActivityTimeline(BaseModel):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="activity_timeline"
    )

    title = models.CharField(
        max_length=255
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    related_model = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    related_object_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    icon = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    metadata = models.JSONField(
        default=dict,
        blank=True
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Activity Timeline"
        verbose_name_plural = "Activity Timeline"
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["related_model", "related_object_id"]),
        ]

    def __str__(self):
        return self.title