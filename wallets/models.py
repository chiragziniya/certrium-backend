import uuid

from django.conf import settings
from django.db import models

from common.models import BaseModel


class Wallet(BaseModel):

    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wallet"
    )

    wallet_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True
    )

    is_public = models.BooleanField(
        default=False,
        db_index=True
    )

    activated_at = models.DateTimeField(
        blank=True,
        null=True
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Wallet"
        verbose_name_plural = "Wallets"
        indexes = [
            models.Index(fields=["owner", "is_active"]),
            models.Index(fields=["owner", "is_public"]),
        ]

    def __str__(self):
        return f"{self.owner.email} Wallet"


class WalletRecord(BaseModel):

    class Visibility(models.TextChoices):
        PRIVATE = "PRIVATE", "Private"
        SHARED = "SHARED", "Shared"
        PUBLIC = "PUBLIC", "Public"

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name="records"
    )

    verification_record = models.ForeignKey(
        "verification.VerificationRecord",
        on_delete=models.CASCADE,
        related_name="wallet_records"
    )

    visibility = models.CharField(
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.PRIVATE,
        db_index=True
    )

    is_revoked = models.BooleanField(
        default=False
    )

    added_at = models.DateTimeField(
        auto_now_add=True
    )

    revoked_at = models.DateTimeField(
        blank=True,
        null=True
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Wallet Record"
        verbose_name_plural = "Wallet Records"
        constraints = [
            models.UniqueConstraint(
                fields=["wallet", "verification_record"],
                name="unique_wallet_verification_record",
            )
        ]
        indexes = [
            models.Index(fields=["wallet", "visibility"]),
            models.Index(fields=["wallet", "is_revoked"]),
            models.Index(fields=["verification_record"]),
        ]

    def __str__(self):
        return f"{self.wallet.owner.email} - {self.verification_record.credential_name}"


class WalletShare(BaseModel):

    class ShareStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        EXPIRED = "EXPIRED", "Expired"
        REVOKED = "REVOKED", "Revoked"

    wallet_record = models.ForeignKey(
        WalletRecord,
        on_delete=models.CASCADE,
        related_name="shares"
    )

    share_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    shared_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wallet_shares_created"
    )

    shared_with_email = models.EmailField()

    expires_at = models.DateTimeField()

    status = models.CharField(
        max_length=20,
        choices=ShareStatus.choices,
        default=ShareStatus.ACTIVE,
        db_index=True
    )

    access_count = models.PositiveIntegerField(
        default=0
    )

    last_accessed_at = models.DateTimeField(
        blank=True,
        null=True
    )

    revoked_at = models.DateTimeField(
        blank=True,
        null=True
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Wallet Share"
        verbose_name_plural = "Wallet Shares"
        indexes = [
            models.Index(fields=["wallet_record", "status"]),
            models.Index(fields=["shared_with_email", "status"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return self.shared_with_email


class WalletAccessLog(BaseModel):

    wallet_share = models.ForeignKey(
        WalletShare,
        on_delete=models.CASCADE,
        related_name="access_logs"
    )

    accessed_by_email = models.EmailField()

    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True
    )

    user_agent = models.TextField(
        blank=True,
        null=True
    )

    accessed_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Wallet Access Log"
        verbose_name_plural = "Wallet Access Logs"
        indexes = [
            models.Index(fields=["wallet_share", "accessed_at"]),
            models.Index(fields=["accessed_by_email", "accessed_at"]),
        ]

    def __str__(self):
        return f"{self.accessed_by_email} accessed wallet"